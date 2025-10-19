#!/usr/bin/env python3
"""
个人网盘系统综合测试脚本
测试所有主要功能是否正常工作
"""

import requests
import json
import os
import tempfile
import time
from typing import Dict, Any


class NetdiskTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token = None
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })
        print(f"{status} {test_name}: {message}")
    
    def test_health_check(self):
        """测试健康检查"""
        try:
            response = requests.get(f"{self.base_url}/health")
            success = response.status_code == 200
            self.log_test("健康检查", success, response.json().get('message', ''))
            return success
        except Exception as e:
            self.log_test("健康检查", False, str(e))
            return False
    
    def test_security_headers(self):
        """测试安全头部"""
        try:
            response = requests.get(f"{self.base_url}/")
            headers = response.headers
            
            required_headers = [
                'x-frame-options',
                'x-content-type-options',
                'x-xss-protection',
                'content-security-policy',
                'x-ratelimit-limit'
            ]
            
            missing_headers = []
            for header in required_headers:
                if header not in headers:
                    missing_headers.append(header)
            
            success = len(missing_headers) == 0
            message = "所有安全头部正常" if success else f"缺少头部: {missing_headers}"
            self.log_test("安全头部", success, message)
            return success
        except Exception as e:
            self.log_test("安全头部", False, str(e))
            return False
    
    def test_login(self):
        """测试用户登录"""
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
            }
            response = requests.post(
                f"{self.base_url}/auth/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get('access_token')
                success = self.access_token is not None
                message = "登录成功，获取到访问令牌" if success else "未获取到访问令牌"
            else:
                success = False
                message = f"登录失败: {response.status_code}"
            
            self.log_test("用户登录", success, message)
            return success
        except Exception as e:
            self.log_test("用户登录", False, str(e))
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """获取认证头部"""
        if self.access_token:
            return {"Authorization": f"Bearer {self.access_token}"}
        return {}
    
    def test_file_list(self):
        """测试文件列表"""
        try:
            response = requests.get(
                f"{self.base_url}/files/browse",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                item_count = len(data.get('items', []))
                message = f"获取文件列表成功，包含{item_count}个项目"
            else:
                message = f"获取文件列表失败: {response.status_code}"
            
            self.log_test("文件列表", success, message)
            return success
        except Exception as e:
            self.log_test("文件列表", False, str(e))
            return False
    
    def test_file_upload(self):
        """测试文件上传"""
        try:
            # 创建临时测试文件
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("这是一个测试文件内容\n测试上传功能")
                temp_file_path = f.name
            
            # 上传文件
            with open(temp_file_path, 'rb') as f:
                files = {'files': ('test_upload.txt', f, 'text/plain')}
                data = {'path': '/'}
                response = requests.post(
                    f"{self.base_url}/files/upload",
                    files=files,
                    data=data,
                    headers=self.get_headers()
                )
            
            # 清理临时文件
            os.unlink(temp_file_path)
            
            success = response.status_code == 200
            if success:
                data = response.json()
                message = data.get('message', '上传成功')
            else:
                message = f"上传失败: {response.status_code}"
            
            self.log_test("文件上传", success, message)
            return success
        except Exception as e:
            self.log_test("文件上传", False, str(e))
            return False
    
    def test_file_search(self):
        """测试文件搜索"""
        try:
            search_params = {
                "keyword": "test",
                "path": "/"
            }
            response = requests.get(
                f"{self.base_url}/files/search",
                params=search_params,
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                result_count = data.get('total', 0)
                message = f"搜索成功，找到{result_count}个结果"
            else:
                message = f"搜索失败: {response.status_code}"
            
            self.log_test("文件搜索", success, message)
            return success
        except Exception as e:
            self.log_test("文件搜索", False, str(e))
            return False
    
    def test_create_directory(self):
        """测试创建目录"""
        try:
            dir_data = {"path": "/test_directory"}
            response = requests.post(
                f"{self.base_url}/files/mkdir",
                json=dir_data,
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                message = data.get('message', '目录创建成功')
            else:
                message = f"创建目录失败: {response.status_code}"
            
            self.log_test("创建目录", success, message)
            return success
        except Exception as e:
            self.log_test("创建目录", False, str(e))
            return False
    
    def test_share_creation(self):
        """测试分享创建"""
        try:
            # 先获取一个文件ID
            response = requests.get(
                f"{self.base_url}/files/browse",
                headers=self.get_headers()
            )
            
            if response.status_code != 200:
                self.log_test("分享创建", False, "无法获取文件列表")
                return False
            
            files = response.json().get('items', [])
            if not files:
                self.log_test("分享创建", False, "没有文件可以分享")
                return False
            
            file_id = files[0]['id']
            
            # 创建分享
            share_data = {
                "file_node_id": file_id,
                "description": "测试分享",
                "expire_hours": 24
            }
            response = requests.post(
                f"{self.base_url}/share/create",
                json=share_data,
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                share_id = data.get('share_id')
                message = f"分享创建成功，ID: {share_id}"
            else:
                data = response.json()
                message = f"分享创建失败: {data.get('detail', response.status_code)}"
            
            self.log_test("分享创建", success, message)
            return success
        except Exception as e:
            self.log_test("分享创建", False, str(e))
            return False
    
    def test_share_list(self):
        """测试分享列表"""
        try:
            response = requests.get(
                f"{self.base_url}/share/list",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                share_count = data.get('total', 0)
                message = f"获取分享列表成功，共{share_count}个分享"
            else:
                message = f"获取分享列表失败: {response.status_code}"
            
            self.log_test("分享列表", success, message)
            return success
        except Exception as e:
            self.log_test("分享列表", False, str(e))
            return False
    
    def test_trash_list(self):
        """测试回收站"""
        try:
            response = requests.get(
                f"{self.base_url}/trash/list",
                headers=self.get_headers()
            )
            
            success = response.status_code == 200
            if success:
                data = response.json()
                item_count = len(data.get('items', []))
                message = f"获取回收站成功，包含{item_count}个项目"
            else:
                message = f"获取回收站失败: {response.status_code}"
            
            self.log_test("回收站列表", success, message)
            return success
        except Exception as e:
            self.log_test("回收站列表", False, str(e))
            return False
    
    def test_rate_limiting(self):
        """测试速率限制"""
        try:
            # 快速发送多个请求
            success_count = 0
            rate_limited_count = 0
            
            for i in range(10):
                response = requests.get(
                    f"{self.base_url}/auth/check",
                    headers=self.get_headers()
                )
                if response.status_code == 200:
                    success_count += 1
                elif response.status_code == 429:
                    rate_limited_count += 1
                time.sleep(0.1)  # 短暂延迟
            
            # 速率限制应该允许正常使用
            success = success_count >= 8  # 至少8个请求成功
            message = f"成功: {success_count}, 被限制: {rate_limited_count}"
            
            self.log_test("速率限制", success, message)
            return success
        except Exception as e:
            self.log_test("速率限制", False, str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始个人网盘系统综合测试\n")
        
        # 基础功能测试
        print("📋 基础功能测试:")
        self.test_health_check()
        self.test_security_headers()
        
        # 认证测试
        print("\n🔐 认证功能测试:")
        if not self.test_login():
            print("❌ 登录失败，跳过需要认证的测试")
            return
        
        # 文件管理测试
        print("\n📁 文件管理测试:")
        self.test_file_list()
        self.test_file_upload()
        self.test_file_search()
        self.test_create_directory()
        
        # 分享功能测试
        print("\n📤 分享功能测试:")
        self.test_share_creation()
        self.test_share_list()
        
        # 回收站测试
        print("\n🗑️ 回收站测试:")
        self.test_trash_list()
        
        # 安全功能测试
        print("\n🔒 安全功能测试:")
        self.test_rate_limiting()
        
        # 总结测试结果
        print("\n📊 测试结果总结:")
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"总计测试: {total_tests}")
        print(f"通过测试: {passed_tests}")
        print(f"失败测试: {failed_tests}")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        success_rate = passed_tests / total_tests
        if success_rate >= 0.9:
            print("\n🎉 系统测试通过！所有主要功能正常工作。")
        elif success_rate >= 0.7:
            print("\n⚠️ 系统基本正常，但有部分功能需要改进。")
        else:
            print("\n💥 系统存在严重问题，需要修复后再次测试。")


if __name__ == "__main__":
    tester = NetdiskTester()
    tester.run_all_tests()