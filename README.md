```python
# pseudocode scheme
from core.markups import WindowBuilder
from core import BotControl


class CustomMessage(WindowBuilder):
    def __init__(self, arg1, kwarg1=None):
        super().__init__()
        self._arg1 = arg1
        self._kwarg1 = kwarg1

    async def init(self):
        print("Initializing logic")


await BotControl(...).dig(CustomMessage("hello", kwarg1="world"))
```
