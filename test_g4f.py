import g4f

try:
    response = g4f.ChatCompletion.create(
        model="openai",
        messages=[{"role": "user", "content": "hello"}],
        provider=g4f.Provider.PollinationsAI
    )
    print(f"PollinationsAI with openai worked!")
    print(response)
except Exception as e:
    print(f"PollinationsAI Error: {e}")
