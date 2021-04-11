import socket
import sys
import argparse
import smtplib
import config

CMD_ARG = '--'
CMD_PRICE = 'price'
CMD_SIGNAL = 'signal'
CMD_SERVER_ADDRESS = 'server_address'
CMD_DEL_TICKER = 'del_ticker'
CMD_ADD_TICKER = 'add_ticker'
CMD_RESET = 'reset'

DEF_HOST = '127.0.0.1'
DEF_PORT = 8000

ERROR_EMAIL = 'email.txt'

def send_error_email():

    sender = config.sender
    receiver = config.receiver
    username = config.email_username
    password = config.email_password

    # not sending email if config isn't set up
    if password == '' or password == 'your password here'
        return

    subject = 'Server does not respond'
    body = 'I think something went wrong with the server'

    email = """\
    From: %s
    To: %s
    Subject: %s

    %s
    """ % (sender, receiver, subject, body)

    server = smtplib.SMTP_SSL('smtp.gmail.com')
    server.ehlo()
    server.login(config.email_username, config.email_password)
    server.sendmail(sender, receiver, email)
    server.close()

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument(CMD_ARG + CMD_PRICE)
    parser.add_argument(CMD_ARG + CMD_SIGNAL)
    parser.add_argument(CMD_ARG + CMD_SERVER_ADDRESS)
    parser.add_argument(CMD_ARG + CMD_DEL_TICKER)
    parser.add_argument(CMD_ARG + CMD_ADD_TICKER)
    parser.add_argument(CMD_ARG + CMD_RESET)

    host = DEF_HOST
    port = DEF_PORT
    args = vars(parser.parse_args())
    serv_args = []

    if args[CMD_PRICE]:
        serv_args.append(CMD_ARG+CMD_PRICE+' '+args[CMD_PRICE])
    
    if args[CMD_SIGNAL]:
        serv_args.append(CMD_ARG+CMD_SIGNAL+' '+args[CMD_SIGNAL])
    
    if args[CMD_DEL_TICKER]:
        serv_args.append(CMD_ARG+CMD_DEL_TICKER+' '+args[CMD_DEL_TICKER])

    if args[CMD_ADD_TICKER]:
        serv_args.append(CMD_ARG+CMD_ADD_TICKER+' '+args[CMD_ADD_TICKER])

    if args[CMD_RESET]:
        serv_args.append(CMD_ARG+CMD_RESET+' '+args[CMD_ADD_TICKER])
    
    if args[CMD_SERVER_ADDRESS]:
        host = args[CMD_SERVER_ADDRESS].split(':')[0]
        port = args[CMD_SERVER_ADDRESS].split(':')[1]

    return host, port, serv_args

def main(host, port, args):

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:

        try:
            s.connect((host, port))
        except:
            send_error_email()
            return -1

        for command in args:
            s.sendall(command.encode())
            serv_response = s.recv(1024).decode('utf-8')

            # return here if only client can only send command line arguments
            # else comment out return for client to continue sending server stdin commands
            return

        while True:
            for client_in in sys.stdin:

                print("Your command is:", client_in)

                s.sendall(client_in.encode())

                serv_response = s.recv(1024).decode('utf-8')

                print(serv_response)

if __name__ == '__main__':
    host, port, args = parse_arguments()
    main(host, port, args)