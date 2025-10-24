#!/bin/bash

# 话单导出调试脚本

echo "🔍 话单导出问题调试"
echo "===================="
echo ""

# 1. 检查数据库中是否有话单数据
echo "1️⃣ 检查数据库中的话单数量..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT vos_id, COUNT(*) as count, MIN(start) as earliest, MAX(start) as latest FROM cdrs GROUP BY vos_id;"

echo ""
echo "2️⃣ 检查最近的话单记录（最多10条）..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT flow_no, account, caller_e164, callee_access_e164, start, stop FROM cdrs ORDER BY start DESC LIMIT 10;"

echo ""
echo "3️⃣ 检查VOS实例信息..."
docker-compose exec postgres psql -U vos_user -d vosadmin -c "SELECT id, name, base_url, enabled FROM vos_instances;"

echo ""
echo "4️⃣ 查看后端日志（最近20行，包含导出相关）..."
docker-compose logs backend --tail=50 | grep -i "导出\|export" || echo "  无导出相关日志"

echo ""
echo "5️⃣ 测试查询话单接口..."
echo "请在浏览器中打开："
echo "  http://服务器IP:8000/docs"
echo "  找到 /api/v1/cdr/export/{instance_id} 接口"
echo "  点击 Try it out 进行测试"

echo ""
echo "💡 调试提示："
echo "  1. 如果数据库中没有话单数据，需要先查询话单让系统同步数据"
echo "  2. 检查查询条件是否过于严格（如账号、主叫号码等）"
echo "  3. 确认查询的时间范围内有数据"
echo "  4. 查看后端日志中的警告信息"
echo ""
echo "📋 常见问题："
echo "  问题1: 查询参数accounts导致查不到数据"
echo "    解决: 清空账号条件，只用时间范围查询"
echo ""
echo "  问题2: 时间范围选择不正确"
echo "    解决: 确保时间范围内有话单数据"
echo ""
echo "  问题3: VOS实例ID不匹配"
echo "    解决: 检查是否选择了正确的VOS节点"
echo ""

