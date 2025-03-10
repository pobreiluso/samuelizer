from abc import ABC, abstractmethod
import requests
import logging
from typing import Dict, Any, Optional

class HttpClientInterface(ABC):
    """
    Interface for HTTP clients to follow Dependency Inversion Principle
    """
    @abstractmethod
    def get(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, **kwargs) -> Any:
        """
        Perform a GET request
        
        Args:
            url: URL to request
            headers: Optional request headers
            params: Optional query parameters
            **kwargs: Additional arguments for the request
            
        Returns:
            Response object with json() method and status_code attribute
        """
        pass
    
    @abstractmethod
    def post(self, url: str, headers: Optional[Dict] = None, data: Optional[Dict] = None, 
             json: Optional[Dict] = None, **kwargs) -> Any:
        """
        Perform a POST request
        
        Args:
            url: URL to request
            headers: Optional request headers
            data: Optional form data
            json: Optional JSON data
            **kwargs: Additional arguments for the request
            
        Returns:
            Response object with json() method and status_code attribute
        """
        pass

class RequestsClient(HttpClientInterface):
    """
    Implementation of HttpClientInterface using the requests library
    """
    def get(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Perform a GET request using requests library
        
        Args:
            url: URL to request
            headers: Optional request headers
            params: Optional query parameters
            **kwargs: Additional arguments for the request
            
        Returns:
            requests.Response object
        """
        return requests.get(url, headers=headers, params=params, **kwargs)
    
    def post(self, url: str, headers: Optional[Dict] = None, data: Optional[Dict] = None, 
             json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Perform a POST request using requests library
        
        Args:
            url: URL to request
            headers: Optional request headers
            data: Optional form data
            json: Optional JSON data
            **kwargs: Additional arguments for the request
            
        Returns:
            requests.Response object
        """
        return requests.post(url, headers=headers, data=data, json=json, **kwargs)
