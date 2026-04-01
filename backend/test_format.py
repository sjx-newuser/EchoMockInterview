template = "Role: {role}\nStage: {stage}"
stage = "Q: {question}"
try:
    res = template.format(role="dev", stage=stage)
    print("SUCCESS:")
    print(res)
except Exception as e:
    print("ERROR:", repr(e))
