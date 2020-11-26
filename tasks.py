import cloudpickle

from pistreaming.app import app

def unpickle_and_run(serialized_object, function_name, *args, **kwargs):
    unpickled_object = cloudpickle.loads(serialized_object)
    output = getattr(unpickled_object, function_name)(*args, **kwargs)
    return output

@app.task(name="run_object_fct", ignore_result=False)
def run_object_fct(serialized_object, function_name, *args, **kwargs):
    return unpickle_and_run(serialized_object, function_name, *args, **kwargs)