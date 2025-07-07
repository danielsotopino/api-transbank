import logging
from typing import Dict, Any, Optional


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        
    def _log(self, level: int, message: str, context: Optional[Dict[str, Any]] = None, 
             error: Optional[Dict[str, Any]] = None):
        extra = {}
        if context:
            extra['context'] = context
        if error:
            extra['error'] = error
            
        self.logger.log(level, message, extra=extra)
    
    def info(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.INFO, message, context)
    
    def warning(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.WARNING, message, context)
    
    def error(self, message: str, context: Optional[Dict[str, Any]] = None, 
              error: Optional[Dict[str, Any]] = None):
        self._log(logging.ERROR, message, context, error)
    
    def debug(self, message: str, context: Optional[Dict[str, Any]] = None):
        self._log(logging.DEBUG, message, context)
    
    def with_cliente(self, cliente_id: int):
        return ContextBuilder(self).with_cliente(cliente_id)
    
    def with_pago(self, pago_id: int):
        return ContextBuilder(self).with_pago(pago_id)
    
    def with_username(self, username: str):
        return ContextBuilder(self).with_username(username)
    
    def with_context(self, key: str, value: Any):
        """Agrega un contexto genérico (clave, valor)."""
        return ContextBuilder(self).with_context(key, value)
    
    def with_contexts(self, **kwargs):
        """Agrega múltiples contextos de una vez."""
        builder = ContextBuilder(self)
        for k, v in kwargs.items():
            builder.with_context(k, v)
        return builder


class ContextBuilder:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.context = {}
    
    def with_cliente(self, cliente_id: int):
        self.context['cliente_id'] = cliente_id
        return self
    
    def with_pago(self, pago_id: int):
        self.context['pago_id'] = pago_id
        return self
    
    def with_monto(self, monto: str):
        self.context['monto'] = monto
        return self
    
    def with_username(self, username: str):
        self.context['username'] = username
        return self
    
    def with_transaction(self, transaction_id: str):
        self.context['transaction_id'] = transaction_id
        return self
    
    def with_context(self, key: str, value: Any):
        """Agrega un contexto genérico (clave, valor)."""
        self.context[key] = value
        return self
    
    def info(self, message: str):
        self.logger.info(message, self.context)
    
    def warning(self, message: str):
        self.logger.warning(message, self.context)
    
    def error(self, message: str, error: Optional[Dict[str, Any]] = None):
        self.logger.error(message, self.context, error)