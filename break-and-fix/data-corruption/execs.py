# -*- coding: utf-8 -*-

# (c) 2015 Jose Angel de Bustos Perez <jadebustos@gmail.com>

# Este módulo proporciona una clase para la ejecución de comandos a nivel de sistema operativo.

import subprocess
import re


class Command:

    # El argumento que recibe el constructor de esta clase es el siguiente:
    # * **command** - comando a ejecutar.

    def __init__(self, command):
        # Comando ejecutado
        self.cmdString = command
        # Ejecutamos el comando
        self.cmd = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Almacenamos la salida estándar y la de errores
        self.stdout, self.stderr = self.cmd.communicate()
        # Almacenamos el estado de finaliación de la ejecución del comando
        self.rc = self.cmd.returncode


    # Este método devuelve la salida de error después de la ejecución del comando como un string.

    def getStderr(self):
        return re.sub('\n$', '', self.stderr)

    # Este método devuelve la salida estándar después de la ejecución del comando como un string.

    def getStdout(self):
        return re.sub('\n$', '', self.stdout)

    # Este método devuelve el código de finalización de la ejecución del comando.

    def getRc(self):
        return self.rc

    # Este método devuelve el comando que se ejecutó.

    def getCmd(self):
        return self.cmdString
