import coup
import logging

if __name__ == "__main__":
    input_buffer = ''
    coup_commander = coup.CoupCommander()
    while input_buffer[0:4].lower() != 'exit':
        input_buffer = raw_input('Input command: ')
        couptext = input_buffer.split(None, 1)
        if len(couptext) > 1:
            username = couptext[0]
            command = couptext[1]
            try:
                result = coup_commander.exec_command(username, 'Public', command)
                if result is not None:
                    for rkey in result.iterkeys():
                        print 'Message to %s -> %s' % (rkey, result[rkey])
            except Exception as e:
                logging.exception('Command %s failed with exception' % command)
    print 'Exiting now'
    exit(0)
