import time

from abc import ABC, abstractmethod
import threading
import asyncio
from typing import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel


class ApiInfo(BaseModel):
    text: str


class Node(ABC):

    def __init__(self, name: str=None, address: str='127.0.0.1', port: int=8000):
        
        self.name = name
        self.is_online: bool = False
        self.is_active: bool = False

        self.app: FastAPI = None
        self.address: str = address
        self.port: int = port

        self.comm_settings: dict = {}
        self.set_comm_settings()

        self._server: uvicorn.Server = None
        self._thread: threading.Thread = None


    @abstractmethod
    def _set_app(self):

        pass


    def set_host(self, address: str, port: int):
        if self.is_online:
            raise ValueError('Cant set host info on active Node!')
        
        self.address = address
        self.port = port

        return
    

    def set_comm_settings(self, latency_s: float=0):

        self.comm_settings['latency_s'] = latency_s

        return
    

    def start(self):

        if self.is_online:
            return
        
        self._set_app()

        config = uvicorn.Config(
            app=self.app,
            host=self.address,
            port=self.port,
            loop='asyncio')
        
        self._server = uvicorn.Server(config=config)

        def run_server():
            asyncio.run(self._server.serve())

        self._thread = threading.Thread(target=run_server, daemon=True)
        self._thread.start()

        self.is_online = True

        return
    

    def stop(self):
        if self.is_online:
            self._server.should_exit = True
            self._thread.join()

            self.app = None
            self.is_online = False
            self._server = None
            self._thread = None

        return
    

class GenericNode(Node):

    def __init__(
        self,
        name: str=None,
        address: str='127.0.0.1',
        port: int=8000,
        callback_is_active: Callable=None):

        super().__init__(name=name, address=address, port=port)

        self.callback_is_active = callback_is_active


    def _set_app(self):

        self.app = FastAPI()

        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=['*'],
            allow_credentials=['*'],
            allow_methods=['*'],
            allow_headers=['*'])

        @self.app.middleware('https')
        async def get_active_requests(request: Request, call_next):

            if self.callback_is_active:
                self.is_active = True
                self.callback_is_active(self)

            response = await call_next(request)

            if self.callback_is_active:
                self.is_active = False
                self.callback_is_active(self)

            return response
        
        
        @self.app.get('/')
        def default():

            time.sleep(self.comm_settings['latency_s'])

            return 'Generic Node.'
        
        return
    

if __name__ == '__main__':

    A = GenericNode()
    A.start()
    time.sleep(10)
    A.stop()

    pass