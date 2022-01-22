from whoami import socket, app
        
if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    socket.run(app, debug=False)