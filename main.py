from cli import *
from options import Server
from APIServer import *
from MessageHandler import *
from multiprocessing import Process, Pipe
import platform

if platform.system() != "Windows":
    from gunicorn.app.base import BaseApplication
    from gunicorn import util
    class StandaloneApplication(BaseApplication):
        def __init__(self, app, options=None):
            self.options = options or {}
            self.application = app
            super().__init__()

        def load_config(self):
            config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
            for key, value in config.items():
                self.cfg.set(key.lower(), value)

        def load(self):
            return self.application

    def run_flask_app(app, host='0.0.0.0', port=8080, workers=1):
        options = {
            'bind': f'{host}:{port}',
            'workers': workers,
        }
        StandaloneApplication(app, options).run()

        #Linux stuff above, because gunicorn is being a bastard

if __name__ == "__main__":
    try:
        cliPipe, botPipe = Pipe()
        messageHandler = MessageHandler(botPipe)
        mhProcess = Process(target=messageHandler.serve)
        mhProcess.start()
        if Server.HOST_SERVER:
            cliPipe.send(['login'])
            app, db_handler = getApp(cliPipe)
            if platform.system() == "Windows":
                app.run(debug=True, host='0.0.0.0', port=8080, use_reloader=False)
            else:
                run_flask_app(app)
        else:
            console = InteractiveConsole(cliPipe)
            console.cmdloop("Dobrodošao u troll prompt hue hue hue!")
    except Exception as e:
        print(e)
        cliPipe.send(['quit'])#try to exit gracefully
        input()
