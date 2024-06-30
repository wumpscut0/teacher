```python
@abyss_router.callback_query(F.data == "back")
async def back(message: Message, bot_control: BotControl):
    await bot_control.back()
```

You can define logic for back button, witch always automatically will set in every appended WindowBuilder by default<br>
For example, you could set dynamic logic for particular WindowBuilder when old instance WindowBuilder will set as back context layer