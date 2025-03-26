from plugins_func.register import register_function, ToolType, ActionResponse, Action

test_reqllm_function_desc = {
    "type": "function",
    "function": {
        "name": "test_reqllm",
        "description": "测试使用大模型回答的插件",
        'parameters': {'type': 'object', 'properties': {
            
        }, 'required': []}
    }
}


@register_function('test_reqllm', test_reqllm_function_desc, ToolType.WAIT)
def test_reqllm():
    # 你的处理流程
    response_text = "现在在调用测试使用大模型回答的插件, 测试已经成功, 请你做出提醒, 以:'恭喜你'开头"
    return ActionResponse(Action.REQLLM, response_text, None)