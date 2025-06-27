import logging
import threading
import queue
import uuid
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from fastmcp import FastMCP

# 配置日志
logger = logging.getLogger('ragflow_mcp')
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 创建任务存储字典和线程池
search_tasks = {}
task_queue = queue.Queue()
executor = ThreadPoolExecutor(max_workers=5)  # 根据服务器性能调整线程数
lock = threading.Lock()  # 用于线程安全的锁

# Create an MCP server
mcp = FastMCP("ragflow_mcp")

# 工作线程函数
def search_worker():
    """后台工作线程，处理搜索任务"""
    while True:
        task_id = task_queue.get()
        if task_id is None:  # 接收到停止信号
            break
            
        try:
            logger.info(f"Processing search task: {task_id}")
            task = search_tasks[task_id]
            question = task["question"]
            
            # 实际搜索请求
            url = "http://localhost/api/v1/retrieval"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer ragflow-Q5MWE2OTJlNTI5OTExZjBiMTcyMDI0Mm"
            }
            data = {
                "question": question,
                "dataset_ids": ["48cb44e0529611f09a230242ac120006"],
                "document_ids": [],
                "highlight": False,
                "similarity_threshold": 0.30,
                "top_k": 64,
                "page_size": 2,
                "return_fields": ["content_ltks", "document_keyword", "similarity"]  # 只返回必要字段
            }
            
            # 发送请求
            start_time = time.time()
            response = requests.post(url, headers=headers, json=data, timeout=30)
            duration = time.time() - start_time
            logger.info(f"Search task {task_id} completed in {duration:.2f}s with status: {response.status_code}")
            
            # 处理响应
            with lock:
                if response.status_code == 200:
                    result = []
                    response_data = response.json()
                    logger.info(f"Response data: {response_data}")
                    for item in response_data.get("data", []).get("chunks", []):
                        # 处理每个结果项
                        logger.info(f"Processing item: {item}")
                        # 只提取必要字段
                        result.append({
                            "content_ltks": item.get("content_ltks", ""),
                            "document_keyword": item.get("document_keyword", ""),
                            "similarity": item.get("similarity", 0.0),
                        })
                    
                    if result:
                        search_tasks[task_id]["status"] = "completed"
                        search_tasks[task_id]["result"] = result
                    else:
                        search_tasks[task_id]["status"] = "completed"
                        search_tasks[task_id]["result"] = []
                        search_tasks[task_id]["message"] = "No results found"
                else:
                    search_tasks[task_id]["status"] = "error"
                    search_tasks[task_id]["error"] = f"API error: {response.status_code} - {response.text[:200]}"
            
        except requests.Timeout:
            with lock:
                search_tasks[task_id]["status"] = "error"
                search_tasks[task_id]["error"] = "Request timed out"
            logger.error(f"Search task {task_id} timed out")
        except Exception as e:
            with lock:
                search_tasks[task_id]["status"] = "error"
                search_tasks[task_id]["error"] = str(e)
            logger.exception(f"Error processing search task {task_id}: {str(e)}")
        finally:
            task_queue.task_done()

# 启动工作线程
for i in range(executor._max_workers):
    executor.submit(search_worker)

@mcp.tool()
def start_search(question: str) -> dict:
    """
    Start Ragflow search task and return task ID for further result retrieval.
    """
    task_id = str(uuid.uuid4())
    logger.info(f"Starting search task {task_id} for question: {question}")
    
    # 初始化任务状态
    with lock:
        search_tasks[task_id] = {
            "status": "queued",
            "question": question,
            "start_time": time.time(),
            "result": None,
            "error": None
        }
    
    # 将任务添加到队列
    task_queue.put(task_id)
    logger.info(f"Task {task_id} added to queue")
    return {"success": True, "task_id": task_id, "status": "queued"}

@mcp.tool()
def get_search_status(task_id: str) -> dict:
    """
    获取任务状态
    """
    with lock:
        task = search_tasks.get(task_id)
    
    if not task:
        return {"success": False, "error": "Task ID not found"}
    
    status_info = {
        "task_id": task_id,
        "status": task["status"],
        "question": task["question"],
        "elapsed_time": time.time() - task["start_time"]
    }
    
    if task["status"] == "error":
        status_info["error"] = task.get("error", "Unknown error")
    
    return {"success": True, **status_info}

@mcp.tool()
def get_search_results(task_id: str) -> dict:
    """
    Retrieve Ragflow search results based on the task ID.
    """
    logger.info(f"Retrieving results for task: {task_id}")
    
    with lock:
        task = search_tasks.get(task_id)
    
    # 检查任务是否存在
    if not task:
        logger.error(f"Task ID {task_id} not found")
        return {"success": False, "error": "Task ID not found"}
    
    # 检查任务状态
    if task["status"] == "queued":
        logger.info(f"Task {task_id} is still in queue")
        return {"success": False, "status": "queued", "message": "Task is still in queue"}
    
    if task["status"] == "processing":
        logger.info(f"Task {task_id} is still processing")
        return {"success": False, "status": "processing", "message": "Search in progress"}
    
    if task["status"] == "error":
        logger.error(f"Task {task_id} encountered an error: {task.get('error', 'Unknown error')}")
        return {"success": False, "status": "error", "error": task.get("error", "Unknown error")}
    
    # 处理完成的任务
    if "result" in task:
        return {
            "success": True,
            "status": "completed",
            "results": task["result"],
            "message": task.get("message", "")
        }
    
    return {"success": False, "error": "Unexpected task state"}

@mcp.tool()
def cancel_search(task_id: str) -> dict:
    """
    取消正在进行的搜索任务
    """
    logger.info(f"Canceling task: {task_id}")
    
    with lock:
        if task_id in search_tasks:
            # 更新状态为取消
            if search_tasks[task_id]["status"] in ["queued", "processing"]:
                search_tasks[task_id]["status"] = "canceled"
                return {"success": True, "message": "Task canceled"}
            else:
                return {"success": False, "error": "Task cannot be canceled in its current state"}
        return {"success": False, "error": "Task ID not found"}

@mcp.tool()
def get_active_tasks() -> dict:
    """
    获取所有活跃任务的信息
    """
    with lock:
        active_tasks = []
        for task_id, task in search_tasks.items():
            if task["status"] in ["queued", "processing"]:
                active_tasks.append({
                    "task_id": task_id,
                    "status": task["status"],
                    "question": task["question"],
                    "elapsed_time": time.time() - task["start_time"]
                })
        
        return {
            "success": True,
            "active_tasks": active_tasks,
            "total_tasks": len(active_tasks)
        }

def cleanup_old_tasks():
    """定期清理旧任务"""
    while True:
        time.sleep(3600)  # 每小时清理一次
        cleanup_time = time.time() - 86400  # 清理24小时前的任务
        
        with lock:
            # 找出需要清理的任务ID
            to_delete = []
            for task_id, task in search_tasks.items():
                if task["start_time"] < cleanup_time:
                    to_delete.append(task_id)
            
            # 删除旧任务
            for task_id in to_delete:
                del search_tasks[task_id]
            
            logger.info(f"Cleaned up {len(to_delete)} old tasks")

# 启动清理线程
cleanup_thread = threading.Thread(target=cleanup_old_tasks, daemon=True)
cleanup_thread.start()

# Start the server
if __name__ == "__main__":
    try:
        logger.info("Starting Ragflow MCP server with threaded search")
        mcp.run(transport="stdio")
    finally:
        # 优雅关闭
        logger.info("Shutting down thread pool...")
        # 发送停止信号给所有工作线程
        for _ in range(executor._max_workers):
            task_queue.put(None)
        executor.shutdown(wait=True)
        logger.info("Thread pool shutdown complete")