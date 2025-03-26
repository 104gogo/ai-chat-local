from plugins_func.register import register_function, ToolType, ActionResponse, Action

test_response_function_desc = {
    "type": "function",
    "function": {
        "name": "test_response",
        "description": "测试直接返回的插件",
        'parameters': {'type': 'object', 'properties': {}, 'required': []}
    }
}


@register_function('test_response', test_response_function_desc, ToolType.WAIT)
def test_response():
    # 你的处理流程
    response_text = "这是一个测试直接返回的插件, 您的测试已经成功"
    return ActionResponse(Action.RESPONSE, None, response_text)