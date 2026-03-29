"""
ABYSSAC记忆MCP - 指令模板 + Reviewer验证
MCP只返回指令，AI执行操作
"""
import json
import sys
from typing import Dict, Any, List


def get_instruction(step: str) -> Dict[str, Any]:
    if step == "ENTRY":
        return {
            "step": "ENTRY",
            "cmd": "CHECK_CACHE_AND_JUDGE",
            "then": [
                "【锚点】缓存是所有判断的依据",
                "",
                "【缓存分片规则】",
                "缓存按范围分片存储，一个范围一个缓存文件",
                "范围可以是：项目/主题/领域/或其他合理分组",
                "范围由AI根据问题语义灵活判断",
                "【严禁】范围不明的缓存，缓存命名必须有实际范围和意义",
                "",
                "1.根据用户问题语义判断属于哪个范围",
                "",
                "2.使用Read工具读取 {ABYSSAC根路径}/ProjectCache/{范围名}.cache.md",
                "",
                "3.文件不存在→缓存miss→跳转R1检索",
                "",
                "4.文件存在→检查状态字段：",
                "   状态=正常→判断缓存内容是否足够回答问题",
                "   状态=待更新→语义判断是否涉及新知识：是→R1 / 否→直接加载",
                "",
                "5.判断是否需要存储（以缓存为锚点）：",
                "   缓存中有对应知识→不需要存储",
                "   缓存中没有对应知识→需要存储",
                "   用户明确要求记住→需要存储",
                "",
                "6.存储内容判断：",
                "   存储：用户要求记住/新知识/用户偏好/项目决策/技术细节",
                "   不存储：寒暄/完全重复/无实质信息"
            ],
            "gate": "缓存命中→DONE / 缓存未命中→R1 / 需要存储→S1",
            "next": {"hit": "DONE", "miss": "R1", "store": "S1"},
            "must_use_tools": ["Read"]
        }
    
    elif step == "R1":
        return {
            "step": "R1",
            "cmd": "TRAVERSE_NNG_ROOT",
            "then": [
                "【循环步骤】遍历所有相关节点，直到没有新相关项",
                "",
                "1.使用Read工具读取 {ABYSSAC根路径}/nng/root.json",
                "",
                "2.提取问题关键词+语义意图",
                "",
                "3.对每个一级节点逐一语义判断：",
                "   与问题有关联吗？",
                "   不确定时默认=有关联",
                "   记录所有有关联的节点路径",
                "",
                "4.继续判断直到所有一级节点都检查完毕",
                "",
                "【输出】所有相关的一级节点路径列表"
            ],
            "gate": "找到相关节点→R2 / 没有相关节点→DONE",
            "next": {"found": "R2", "not_found": "DONE"},
            "must_use_tools": ["Read"]
        }
    
    elif step == "R2":
        return {
            "step": "R2",
            "cmd": "TRAVERSE_NNG_NODE",
            "then": [
                "【循环步骤】深入遍历每个相关节点，直到没有新相关项",
                "",
                "对R1找到的每个节点：",
                "",
                "1.使用Read工具读取 {ABYSSAC根路径}/{节点路径}",
                "",
                "2.检查'已更新'字段：",
                "   有→跳转到新节点路径读取",
                "",
                "3.检查load_rule：",
                "   when匹配→应该加载",
                "   not_when匹配→跳过",
                "   都不匹配→默认加载",
                "",
                "4.遍历下级关联NNG：",
                "   对每个下级节点语义判断是否相关",
                "   相关→递归读取并继续遍历",
                "   不相关→跳过",
                "",
                "5.收集所有关联的记忆文件摘要中的记忆路径",
                "",
                "6.继续遍历直到没有新的相关下级节点",
                "",
                "【输出】所有相关的记忆路径列表"
            ],
            "gate": "找到记忆路径→R3 / 没有记忆路径→DONE",
            "next": {"found": "R3", "not_found": "DONE"},
            "must_use_tools": ["Read"]
        }
    
    elif step == "R3":
        return {
            "step": "R3",
            "cmd": "LOAD_MEMORY",
            "then": [
                "【循环步骤】读取所有相关记忆，AI决定哪些写入缓存",
                "",
                "对R2找到的每个记忆路径：",
                "",
                "1.使用Read工具读取 {ABYSSAC根路径}/{记忆路径}",
                "",
                "2.读取完整内容（不是摘要）",
                "",
                "3.检查instruction中的IF条件：",
                "   匹配→执行对应行动",
                "",
                "4.继续读取直到所有相关记忆都加载完毕",
                "",
                "5.AI判断哪些记忆与问题相关：",
                "   相关→保留，写入缓存",
                "   不相关→不写入缓存",
                "",
                "6.按置信度排序保留的记忆：",
                "   高≥90 > 中70-89 > 低<70",
                "",
                "【输出】AI筛选后的记忆列表（准备写入缓存）"
            ],
            "gate": "成功加载→R4 / 没有记忆→DONE",
            "next": {"found": "R4", "not_found": "DONE"},
            "must_use_tools": ["Read"]
        }
    
    elif step == "R4":
        return {
            "step": "R4",
            "cmd": "WRITE_CACHE",
            "then": [
                "【缓存分片规则】",
                "缓存按范围分片存储，一个范围一个缓存文件",
                "范围可以是：项目/主题/领域/或其他合理分组",
                "范围由AI根据检索内容和问题语义灵活判断",
                "【严禁】范围不明的缓存，缓存命名必须有实际范围和意义",
                "",
                "1.根据检索内容和问题语义判断缓存范围",
                "",
                "2.使用Read工具读取现有缓存 {ABYSSAC根路径}/ProjectCache/{范围名}.cache.md",
                "",
                "3.在现有缓存基础上添加新检索到的内容（不重复）",
                "",
                "4.每个记忆必须包含完整内容，不是摘要",
                "",
                "5.元认知记忆优先，其余按命中顺序",
                "",
                "6.使用Write工具写入更新后的缓存",
                "",
                "7.以缓存为上下文回答用户"
            ],
            "next": {"complete": "REVIEW_R"},
            "must_use_tools": ["Read", "Write"],
            "cache_format": [
                "# ProjectCache: {范围名}",
                "生成时间: {ISO8601}",
                "状态: 正常",
                "",
                "## 记忆内容",
                "",
                "#### {记忆ID}",
                "置信度: {置信度}",
                "{完整记忆内容}",
                "",
                "## NNG路径索引",
                "{命中的NNG节点树形结构}"
            ],
            "important": "缓存必须包含完整记忆内容，不是摘要！更新时在现有基础上添加，不删除已有内容！按范围分片存储！"
        }
    
    elif step == "REVIEW_R":
        return {
            "step": "REVIEW_R",
            "cmd": "REVIEW_RETRIEVE",
            "then": [
                "🔴必须通过：",
                "□ root.json已读取？",
                "□ 一级节点逐一判断？",
                "□ 已更新节点已跳转？",
                "□ 记忆文件完整读取？",
                "□ ProjectCache已生成？",
                "□ 缓存包含完整记忆内容（不是摘要）？",
                "□ 缓存是在现有基础上添加（没删除已有内容）？",
                "",
                "🟡应该通过：",
                "□ 下级节点逐一判断？",
                "□ load_rule正确匹配？",
                "",
                "🟢建议通过：",
                "□ 记忆按置信度排序？"
            ],
            "gate": "🔴全部通过→DONE / 🔴有未通过→返回对应步骤",
            "next": {"pass": "DONE", "fail_root": "R1", "fail_traverse": "R2", "fail_load": "R3", "fail_cache": "R4"}
        }
    
    elif step == "S1":
        return {
            "step": "S1",
            "cmd": "JUDGE_AND_LOCATE",
            "then": [
                "【输入】用户对话内容",
                "【输出】完整存储决策 + 重复检查结果",
                "",
                "【一次性读取root.json，完成所有判断】",
                "",
                "1.使用Read读取 {ABYSSAC根路径}/nng/root.json",
                "",
                "2.判断是否值得存储：",
                "   存储：用户要求记住/新知识/用户偏好/项目决策/技术细节",
                "   不存储：寒暄/完全重复/无实质信息",
                "",
                "3.确定记忆类型（三选一）：",
                "   元认知：推理策略/系统性错误/能力边界",
                "   高阶整合：跨领域知识整合",
                "   分类：具体领域知识/用户偏好/项目决策",
                "",
                "4.确定价值层级和置信度范围：",
                "   高：核心/强调内容 → 置信度90-100",
                "   中：一般内容 → 置信度70-89",
                "   低：辅助内容 → 置信度50-69",
                "",
                "5.确定NNG父节点路径：",
                "   根据内容语义判断应归属的一级节点",
                "   如无合适节点则创建新一级节点",
                "",
                "6.生成摘要（5-20字）：概括核心内容",
                "",
                "7.检查重复（基于已读取的root.json）：",
                "   检查是否有相同或相似摘要的一级节点",
                "   如有，Read读取该节点检查下级节点",
                "   使用Glob搜索 {ABYSSAC根路径}/Y层记忆库/**/*.txt",
                "   有相似文件则Read检查内容是否重复",
                "",
                "8.判断重复类型：",
                "   完全重复：内容完全相同 → 跳过存储",
                "   部分重复：有补充信息 → 在现有NNG添加关联",
                "   矛盾过时：新内容与旧内容矛盾 → 创建新节点+旧节点标记已更新",
                "   全新：无相似内容 → 创建新节点"
            ],
            "output": {
                "值得存储": "是/否",
                "记忆类型": "元认知/高阶整合/分类",
                "价值层级": "高/中/低",
                "置信度范围": "90-100 / 70-89 / 50-69",
                "NNG父节点路径": "nng/{父节点}/",
                "摘要": "{5-20字}",
                "重复类型": "完全重复/部分重复/矛盾过时/全新",
                "旧NNG路径": "nng/{旧节点}.json（如有）",
                "旧记忆路径": "Y层记忆库/...（如有）"
            },
            "gate": "完全重复→DONE / 值得存储→S2 / 不值得存储→DONE",
            "next": {"store": "S2", "skip": "DONE"},
            "must_use_tools": ["Read", "Glob"]
        }
    
    elif step == "S2":
        return {
            "step": "S2",
            "cmd": "GENERATE_PATH_AND_ID",
            "then": [
                "【输入】S1的类型/层级/摘要/重复类型",
                "【输出】完整路径 + 记忆ID + 置信度具体值",
                "",
                "1.生成记忆ID：YYYYMMDDHHmmss + 3位序号",
                "",
                "2.确定记忆文件路径：",
                "   元认知：{ABYSSAC根路径}/Y层记忆库/元认知记忆/{year}/{month}/{day}/{id}.txt",
                "   高阶整合：{ABYSSAC根路径}/Y层记忆库/高阶整合记忆/{year}/{month}/{day}/{id}.txt",
                "   分类：{ABYSSAC根路径}/Y层记忆库/分类记忆/{层级}/{year}/{month}/{day}/{id}.txt",
                "",
                "3.确定NNG节点路径：",
                "   {ABYSSAC根路径}/nng/{父节点}/{摘要}.json",
                "",
                "4.确定置信度具体值（在S1范围内选）：",
                "   根据内容重要性、准确性、时效性综合判断"
            ],
            "output": {
                "记忆ID": "{YYYYMMDDHHmmss + 3位序号}",
                "记忆文件路径": "{完整路径}",
                "NNG节点路径": "{完整路径}",
                "置信度": "{具体数字}"
            },
            "next": {"continue": "S3"}
        }
    
    elif step == "S3":
        return {
            "step": "S3",
            "cmd": "WRITE_MEMORY_AND_NNG",
            "then": [
                "【输入】S1的摘要/父节点/重复类型/旧NNG路径 + S2的路径/ID/置信度 + 用户对话内容",
                "【输出】记忆文件+NNG节点写入完成",
                "",
                "【第一步：写记忆文件】",
                "使用Write工具写入 {S2记忆文件路径}",
                "必须包含完整内容，禁止只存摘要",
                "",
                "【第二步：写NNG节点】",
                "根据S1的重复类型执行：",
                "",
                "【NNG更新核心规则】",
                "旧NNG只能新增内容，禁止删减任何字段",
                "下级NNG必须是独立的NNG文件",
                "下级NNG必须在'上级关联NNG'中关联父节点",
                "",
                "【全新】创建新NNG节点：",
                "使用Write创建 {ABYSSAC根路径}/nng/{父节点路径}/{摘要}.json",
                "",
                "【部分重复】在现有NNG添加关联：",
                "Read读取旧NNG → 在'关联的记忆文件摘要'数组添加新记忆 → Write写入",
                "【严禁】删除旧NNG中的任何内容",
                "",
                "【矛盾过时】创建新NNG + 旧NNG标记已更新：",
                "Write创建新NNG → Read读取旧NNG → 添加'已更新'字段 → Write写入旧NNG"
            ],
            "memory_format": [
                "记忆层级: {S1类型}",
                "记忆ID: {S2的ID}",
                "记忆时间: {当前ISO8601}",
                "置信度: {S2的置信度}",
                "",
                "{用户对话的完整内容}",
                "",
                "instruction:",
                "- IF {具体条件} THEN {明确行动}"
            ],
            "nng_new_template": {
                "定位": "{S1的摘要}",
                "置信度": "{S2的置信度}",
                "时间": "{当前ISO8601}",
                "内容": "{核心内容≤100字}",
                "instruction": ["IF {条件} THEN {行动}"],
                "load_rule": {"when": ["{场景}"], "not_when": ["{场景}"]},
                "上级关联NNG": [{"节点ID": "{父节点摘要}", "路径": "nng/{父节点路径}.json"}],
                "下级关联NNG": [],
                "关联的记忆文件摘要": [{"记忆ID": "{S2的ID}", "路径": "{S2记忆路径}", "摘要": "{20-50字}"}]
            },
            "nng_update_rules": {
                "只能新增": "在现有数组中添加新元素，不删除已有元素",
                "标记已更新": "添加'已更新'字段，不删除其他内容"
            },
            "next": {"continue": "S4"},
            "must_use_tools": ["Read", "Write"],
            "important": "旧NNG只能新增不能删减！记忆文件必须包含完整内容！"
        }
    
    elif step == "S4":
        return {
            "step": "S4",
            "cmd": "UPDATE_INDEX",
            "then": [
                "【输入】S1的摘要 + S2的NNG路径",
                "【输出】root.json更新 + 缓存标记待更新",
                "",
                "1.使用Read读取 {ABYSSAC根路径}/nng/root.json",
                "",
                "2.如果是一级节点：",
                "   在'一级节点'数组中添加: '{摘要}:{NNG路径}:{内容简述}'",
                "",
                "3.如果是下级节点：",
                "   Read读取父节点 → 在'下级关联NNG'中添加引用 → Write写入父节点",
                "",
                "4.使用Write写入更新后的root.json",
                "",
                "5.使用Read读取 {ABYSSAC根路径}/ProjectCache/{范围名}.cache.md",
                "",
                "6.将缓存头部'状态'字段改为'待更新'",
                "",
                "7.使用Write写入更新后的缓存"
            ],
            "output": {
                "root.json": "已更新",
                "缓存状态": "待更新"
            },
            "next": {"complete": "REVIEW_S"},
            "must_use_tools": ["Read", "Write"],
            "important": "存储后只标记缓存待更新，不写入缓存内容"
        }
    
    elif step == "REVIEW_S":
        return {
            "step": "REVIEW_S",
            "cmd": "REVIEW_STORE",
            "then": [
                "🔴必须通过：",
                "□ S1判断完整（价值+类型+层级+父节点+摘要+重复检查）？",
                "□ root.json只读取一次（S1）？",
                "□ 记忆文件包含完整内容？",
                "□ NNG节点已创建/更新？",
                "□ NNG与记忆双向关联？",
                "□ root.json已更新？",
                "□ 记忆ID唯一？",
                "□ 缓存只标记待更新？",
                "",
                "🟡应该通过：",
                "□ instruction具体可执行？",
                "□ 价值层级与置信度一致？",
                "",
                "🟢建议通过：",
                "□ 标签准确？"
            ],
            "gate": "🔴全部通过→DONE / 🔴有未通过→返回对应步骤",
            "next": {"pass": "DONE", "fail_judge": "S1", "fail_path": "S2", "fail_write": "S3", "fail_index": "S4"}
        }
    
    elif step == "DONE":
        return {
            "step": "DONE",
            "cmd": "END",
            "then": ["流程完成"]
        }
    
    return {"error": f"未知步骤: {step}"}


class MCPWorkflowServer:
    def run(self):
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self.handle_request(request)
                print(json.dumps(response, ensure_ascii=False), flush=True)
            except Exception as e:
                print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}}, ensure_ascii=False), flush=True)
    
    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "abyssac-memory",
                        "version": "1.0.0",
                        "description": "ABYSSAC记忆系统MCP"
                    }
                }
            }
        
        elif method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "mcp_instruction",
                            "description": "获取指定步骤的指令模板。步骤: ENTRY, R1-R4, REVIEW_R, S1-S4, REVIEW_S, DONE",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "step": {"type": "string", "description": "步骤: ENTRY, R1-R4, REVIEW_R, S1-S4, REVIEW_S, DONE"}
                                },
                                "required": ["step"]
                            }
                        }
                    ]
                }
            }
        
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_params = params.get("arguments", {})
            
            if tool_name == "mcp_instruction":
                step = tool_params.get("step", "")
                result = get_instruction(step)
            else:
                return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Tool not found"}}
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False, indent=2)}]}
            }
        
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}


def main():
    server = MCPWorkflowServer()
    server.run()


if __name__ == "__main__":
    main()
