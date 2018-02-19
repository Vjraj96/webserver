#!/usr/bin/python

import signal  # Internal signal processing
import subprocess  # Scripting
import sys  # duh
import socket  # duh
import threading  # To permit concurrent client connections
import json  # To read config files
import logging  # yep this is here too.


def getRequest(method):
    """
    GET request handler
    """
    print(method)
    global root
    code = "200"
    if method == "":
        method = "index.html"
    try:
        with open(root + method) as f:
            page = f.read()
    except (IOError, OSError) as e:
        if e.errno == 2:  # File not found
            code = "404"
        elif e.errno == 13:  # Permission denied
            code = "403"
        else:
            code = "500"
        with open(root + code + ".html") as f:
            page = f.read()
    return code, page


def postRequest():
    """
    POST request handler
    """
    pass


def connectRequest():
    """
    CONNECT request handler
    """
    pass


def putRequest():
    """
    PUT request handler
    """
    pass


def deleteRequest(method, filepath, version):
    """
    DELETE request handler
    """
    if method == "DELETE":
        if my_file.exists(filepath):
            os.remove(filepath)
            code = 200
            return version code phrase
        else:
            code = 204
            return version code phrase
   


def getResponse(method, headers, body):
    """
    Generates HTTP response for a request
    Params:
        request: an un-sanitized string containing the user's request.
    Return:
        String containing response code
    Potential codes:
        200, All is well
        400, Bad request
        401, Unauthorized
        _403_, Forbidden
        _404_, File not found
        411, Length required
        _500_, Internal server error
        505 HTTP version not supported
    """
    global disabled
    if method[2] != "HTTP/1.1":
        code = "505"
        body = "HTTP version not supported"
        return "HTTP/1.1 " + code + "\r\n\r\n" + body
    if method[0] == "GET" and "GET" not in disabled:
        code, body = getRequest(method[1])
    elif method[0] == "POST" and "POST" not in disabled:
        pass
    elif method[0] == "PUT" and "PUT" not in disabled:
        pass
    elif method[0] == "DELETE" and "DELETE" not in disabled:
        pass
    elif method[0] == "CONNECT" and "CONNECT" not in disabled:
        pass
    else:
        code = "500"
        with open(root + code + ".html") as f:
            page = f.read()
    return "HTTP/1.1 " + code + "\r\n\r\n" + body


def getHeaders(headerlist):
    """
    Isolates headers in un-sanitized input
    Params:
        headerlist: an un-sanitized list containing the user's header options.
    Return:
        Dictionary of headers
    """
    dic = {}
    for header in headerlist:
        header = header.split(":")
        for item in header:
            item = item.strip()
        dic[header[0]] = header[1]
    return dic


def getPhp(phpfile):
    """
    Isolates headers in un-sanitized input
    Params:
        page: a file that the web server is hosting.
    Return:
        The whole file as a string
    """
    result = subprocess.check_output(["php", page])
    return result


def parseRequest(request):
    """
    Generates HTTP response for a request
    Params:
        request: an un-sanitized string containing the whole user request.
    Returns:
        (method, headers, body)
    """
    try:
        request = request.split("\r\n\r\n")
        headers = request[0]
        headers = headers.split("\r\n")
        method = headers[0].split(" ")
        method[1] = method[1][1:]
    except:
        return
    headers = getHeaders(headers[1:])  # This will change headers to a dictionary.
    return(method, headers, request[1:])


def getConfig(configfile):
    """
    Retrieve configuration from settings file
    Params:
        configfile: String containing config file name
    Return:
        Dictionary linking settings keywords to definitions
    """
    with open(configfile) as f:
        data = json.load(f)  # load the whole config file
    return data


def requestHandler(client, goodlog, badlog):
    """
    A thread used to parse and respond to a particular HTTP request.
    Params:
        client - a socket object representing the client.
    Return:
        None
    """
    method, headers, body = parseRequest(client.recv(65535))
    response = getResponse(method, headers, body)

    client.send(response)
    # Because HTTP is connectionless we close the connection at the end of every action
    client.close()


def initLogs(glog, blog):
    """
    Initializes logger objects from given strings
    Params:
        goodlog: string of good log file location
        badlog: string of bad log file location
    Return:
        (goodlog, badlog)
    """
    # Set up both log file outputs
    goodlog = logging.getLogger('good_logs')  # set up logger for easy logging.
    goodhdlr = logging.FileHandler(glog)
    goodformatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    goodhdlr.setFormatter(goodformatter)
    goodlog.addHandler(goodhdlr)
    goodlog.setLevel(logging.INFO)
    badlog = logging.getLogger('bad_logs')  # set up logger for easy logging.
    badhdlr = logging.FileHandler(blog)
    badformatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    badhdlr.setFormatter(badformatter)
    badlog.addHandler(badhdlr)
    badlog.setLevel(logging.INFO)
    return (goodlog, badlog)


def main():
    """
    Basic web server implementing  GET, POST, PUT, DELETE, and CONNECT
    with the basic error reporting codes and a scripting language.
    Return:
        None
    """
    try:
        conf = getConfig(sys.argv[1])
    except IndexError:
        print("Defaulting to \"./webserver.blob\"")
        conf = getConfig("webserver.blob")

    if conf["root"][-1] != "/":
        conf["root"] += "/"
    global root
    root = conf["root"]
    goodlog, badlog = initLogs(conf["goodlog"], conf["badlog"])

    global disabled
    disabled = conf["disabled"]

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def signal_handler(signal, frame):
            print('\nClosing server.\n')
            s.close()
            sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        s.bind((conf["host"], int(conf["port"])))  # Bind to port
    except socket.error, e:
        print("Could not bind to port: " + str(e))
        sys.exit(1)

    s.listen(10)  # concurrent connections possible

    try:
        while(True):
            # Client is an object representing the client
            # adr is an array of information about the client
            client, adr = s.accept()  # Accept is a blocking call
            goodlog.info("New connection from {0}:{1}".format(adr[0], adr[1]))

            # requestHandler is the function being run in the thread
            # args are the parameters it takes
            # You need the comma because it needs to be iterable
            threading.Thread(target=requestHandler, args=(client, goodlog, badlog)).start()

    except socket.error, exc:
        badlog.error("Caught exception socket.error: {}".format(exc.message))


if __name__ == "__main__":
    main()
