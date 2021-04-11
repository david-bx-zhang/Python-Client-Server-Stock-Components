import socket
import sys
import select
import argparse
import signal
import pandas as pd

from Server import Server
from Ticker import Ticker
from AlphaVantage import AlphaVantage
from Finnhub import FinnHub

HOST = '127.0.0.1'

CMD_ARG = '--'
CMD_PORT = 'port'
CMD_TICKERS = 'tickers'
CMD_RELOAD = 'reload'
CMD_MINUTES = 'minutes'

DEF_TICKERS = ['AAPL']
DEF_MINUTES = 5
DEF_PORT = 8000

def parse_arguments():
    parser = argparse.ArgumentParser()

    # supported arguments
    ## e.g. --tickers AAPL,IBM
    ##      --port 8000
    ##      --reload file.csv
    ##      --minutes 5
    parser.add_argument(CMD_ARG + CMD_TICKERS, help='optional, default is AAPL, max 3 tickers')
    parser.add_argument(CMD_ARG + CMD_PORT, help='optional, default is 8000')
    parser.add_argument(CMD_ARG + CMD_RELOAD, help='optional, default load from AlphaVantage API')
    parser.add_argument(CMD_ARG + CMD_MINUTES, help='optional, default is 5')

    tickers = DEF_TICKERS
    minutes = DEF_MINUTES
    port = DEF_PORT
    source = None

    args = vars(parser.parse_args())

    # parse command line arguments
    if args[CMD_TICKERS]:
        tickers = args[CMD_TICKERS].split(',')

    if args[CMD_MINUTES]:
        minutes = int(args[CMD_MINUTES])
    
    if args[CMD_PORT]:
        port = int(args[CMD_PORT])

    if args[CMD_RELOAD]:
        source = args[CMD_RELOAD]

    return {'tickers': tickers, 'minutes': minutes, 'port': port, 'reload': source}

def dict_to_str(dict):

    # output format:
    #
    # AAPL   332.50
    #
    # IBM    180.30
    #

    out = ''
    err_count = 0

    for key, value in dict.items():
        out += str(key)
        
        for i in range(7 - len(str(key))):
            out += ' '
        
        if value == -1:
            out += 'No Data \n\n'
            err_count += 1
        else:
            out += str(value) + '\n\n'

    if err_count == len(dict.keys()):
        out = 'Server has no data\n'
    
    return out[:-1]

def main(args):

    # read in args
    port = args[CMD_PORT]
    source = args[CMD_RELOAD]
    minutes = args[CMD_MINUTES]
    tickers = args[CMD_TICKERS]

    cur_ticker_list = tickers

    # ctrl+c -> quit with exit code 0
    signal.signal(signal.SIGINT, lambda x, y: sys.exit(0))

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen(4)

        print("Starting up server")

        # read from file (only one file for one ticker supported) or AlphaVantage API
        if source:
            sv = Server(tickers, minutes, source)
        else:
            sv = Server(tickers, minutes)

        print("Server started")

        print("Server now awaiting client connection")

        inputSockets = [s, sys.stdin]
        baseSockets = inputSockets
        
        while True:
            
            input_ready, output_ready, except_ready = select.select(inputSockets, [], [])

            for x in input_ready:

                # waiting for connections:
                if x == s:
                    
                    connection, address = s.accept()
                    print('Connected by', address)
                    inputSockets.append(connection)

                # server command line arguments
                elif x == sys.stdin:

                    server_in = sys.stdin.readline().strip()

                    # allowing for stdin
                    if server_in == '--price now':
                        dict_to_str
                        out = sv.get_price_at('now')
                        print(dict_to_str(out))

                # commands from client
                else:
                    try:
                        data = x.recv(1024).decode('utf-8')
                    except socket.error as e:

                        # client disconnect
                        print('Broken pipe:', e)
                        inputSockets.remove(x)
                        print('Most likely client disconnected')
                        break

                    print("Received call from client:" + str(address) + " with command:" + data)
                    serv_response = 'Server has no data'
                    print('Server last updated at:' + str(sv.get_last_updated()))

                    # supported client commands
                    ## --price 2020-04-09-13:30
                    ## --price now
                    ## --signal 2020-04-09-13:30
                    ## --signal now
                    ## --del_ticker TICKER
                    ## --add_ticker TICKER
                    ## --reset
                    if '--price' in data:

                        if data.strip() == '--price now':
                            serv_response = dict_to_str(sv.get_price_at('now'))
                            print(serv_response)

                        else:
                            try:
                                ts = data.strip().split(' ')[1]
                                serv_response = dict_to_str(sv.get_price_at(str(pd.to_datetime(ts))))
                                print(serv_response)

                                if serv_response == -1:
                                    serv_response = 'Server has no data'
                            except:
                                print('Error in --price call')

                    elif '--signal' in data:
                        
                        if data.strip() == '--signal now':
                            serv_response = dict_to_str(sv.get_signal_at('now'))
                            print(serv_response)
                        
                        else:
                            try:
                                ts = data.strip().split(' ')[1]
                                serv_response = dict_to_str(sv.get_signal_at(str(pd.to_datetime(ts))))
                                print(serv_response)

                                if serv_response == -1:
                                    serv_response = 'Server has no data'
                            except:
                                print('Error in --signal call')
                    
                    elif '--del_ticker' in data:

                        try:
                            ticker = data.strip().split(' ')[1]
                            serv_response = str(sv.delete_ticker(ticker))
                            cur_ticker_list.append(ticker)
                            print(serv_response)
                        except:
                            serv_response = str(1)
                            print('Error in --del_ticker call')

                    elif '--add_ticker' in data:

                        try:
                            ticker = data.strip().split(' ')[1]
                            serv_response = str(sv.download_tickers([ticker]))
                            cur_ticker_list.remove(ticker)
                            print(serv_response)
                        except:
                            serv_response = str(1)
                            print('Error in --add_ticker call')

                    elif '--reset' in data:

                        try:
                            sv = Server(cur_ticker_list, minutes)
                            serv_response = str(0)
                        except:
                            serv_response = str(1)
                    
                    else:
                        serv_response = 'Unsupported command'
                        serv_response += 'please send a command in one of the following forms\n'
                        serv_response += '--price YYYY-MM-DD-HH:MM or --price now\n'
                        serv_response += '--signal YYYY-MM-DD-HH:MM or --signal now\n'
                        serv_response += '--del_ticker TICKER\n'
                        serv_response += '--add_ticker TICKER\n'
                        serv_response += '--reset\n'
                    
                    try:
                        x.sendall(serv_response.encode())
                    except socket.error as e:
                        print('Broken pipe:', e)
                        print('Most likely client disconnected')
                    

                    


if __name__ == '__main__':
    args = parse_arguments()
    main(args)
