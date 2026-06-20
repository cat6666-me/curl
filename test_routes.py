"""
测试脚本：验证自动回复 API 路由是否正确注册
"""
import sys
sys.path.insert(0, '.')

from web.server import WebServer

class DummyBot:
    """模拟机器人对象"""
    def get_guild(self, guild_id):
        return None

# 创建 WebServer 实例
print("创建 WebServer 实例...")
server = WebServer(DummyBot(), port=8080)

# 检查路由是否已注册
print("\n已注册的路由:")
print("=" * 60)

auto_reply_routes = []
for route in server.app.router.routes():
    route_info = str(route.resource)
    if 'auto-reply' in route_info or 'auto_reply' in route_info:
        auto_reply_routes.append({
            'method': route.method,
            'path': route_info
        })
        print(f"{route.method:8} {route_info}")

print("\n" + "=" * 60)
print(f"找到 {len(auto_reply_routes)} 个自动回复相关路由")

if len(auto_reply_routes) > 0:
    print("\n✅ 自动回复路由已正确注册！")
    print("\n预期应该有 6 个路由:")
    print("  GET    /api/auto-reply/{guild_id}")
    print("  POST   /api/auto-reply/{guild_id}")
    print("  PUT    /api/auto-reply/{guild_id}/{rule_id}")
    print("  DELETE /api/auto-reply/{guild_id}/{rule_id}")
    print("  POST   /api/auto-reply/{guild_id}/toggle")
    print("  POST   /api/auto-reply/{guild_id}/{rule_id}/toggle")
else:
    print("\n❌ 没有找到自动回复路由！")
    print("   可能的原因：")
    print("   1. 代码没有正确保存")
    print("   2. 缩进错误导致路由没有被添加")
    print("   3. setup_routes() 方法有问题")

# 列出所有 API 路由
print("\n\n所有 API 路由:")
print("=" * 60)
for route in server.app.router.routes():
    route_info = str(route.resource)
    if '/api/' in route_info:
        print(f"{route.method:8} {route_info}")
