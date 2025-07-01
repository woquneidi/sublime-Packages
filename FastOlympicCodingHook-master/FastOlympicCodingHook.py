import sublime
import sublime_plugin
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import _thread
import threading
import os
from os import path
from datetime import datetime
import traceback

def slugify(name):
    if not isinstance(name, str):
        name = str(name) if name is not None else "untitled"
    return ''.join(c if c.isalnum() or c in ['_', '-'] else '_' for c in name).strip('_')

def make_cpp_template(name, url, contestname, time_limit, memory_limit, group):
    return (
        "#include<bits/stdc++.h>\n"
        "using namespace std;\n"
        "using i64 = long long;\n\n\n"
        "void solve(){{\n"
        "\t\n"
        "\n"
        "\n"
        "\n"
        "\n"
        "\t\n"
        "}}\n\n\n"
        "int main(){{\n"
        "\tstd::ios::sync_with_stdio(false), cin.tie(0), cout.tie(0);\n\n"
        "\tint T = 1;\n"
        "\t//cin >> T;\n"
        "\twhile(T--) solve();\n\n"
        "\treturn 0;\n"
        "}}\n"
    ).format(name=name, url=url, contestname=contestname, time_limit=time_limit, memory_limit=memory_limit, group=group)

def MakeHandlerClass(foc_settings):
    tests_file_suffix = foc_settings.get("tests_file_suffix", "_tests.txt")
    use_title = foc_settings.get("use_title_as_filename", True)

    # 基于日期的输出路径（用于其他平台）
    today = datetime.today()
    base_dir = os.path.expanduser("~/c++")
    cpp_output_dir = os.path.join(
        base_dir,
        "program_{:04d}".format(today.year),
        "program_{:02d}".format(today.month),
        "program_{:02d}".format(today.day)
    )
    test_output_dir = os.path.join(base_dir, "data", "input")

    class HandleRequests(BaseHTTPRequestHandler):
        def do_POST(self):
            try:
                content_length = int(self.headers['Content-Length'])
                body = self.rfile.read(content_length)
                data = json.loads(body.decode('utf8'))

                # 字段防御
                title = data.get("title") or "untitled"
                name = data.get("name") or "Unknown Problem"
                url = data.get("url", "")
                group = data.get("group", "")
                contestname = data.get("contestname", "")
                time_limit = data.get("timeLimit", 1000)
                memory_limit = data.get("memoryLimit", 256)
                tests = data.get("tests", [])

                # 判断是否为指定平台（含AtCoder）
                is_special_platform = group in ["Codeforces", "NowCoder", "Luogu"] or (group.startswith("AtCoder"))
                
                if is_special_platform:
                    # AtCoder特殊处理：group和contestname都从group字段提取
                    if group.startswith("AtCoder"):
                        if " - " in group:
                            parts = group.split(" - ", 1)
                            group_dir = slugify(parts[0].strip())
                            contestname_dir = slugify(parts[1].strip())
                        else:
                            group_dir = slugify(group)
                            contestname_dir = "problem"
                    else:
                        group_dir = slugify(group)
                        contestname_dir = slugify(contestname) if contestname else "problem"
                    name_file = slugify(name)
                    
                    special_base_dir = r"D:\wqnd\Desktop\ACM"
                    cpp_output_dir = os.path.join(special_base_dir, group_dir, contestname_dir)
                    filename_base = name_file
                    test_output_dir = os.path.join(special_base_dir, group_dir, contestname_dir)
                else:
                    # 其他平台：从group中提取比赛信息
                    special_base_dir = r"D:\wqnd\Desktop\ACM"
                    if " - " in group:
                        parts = group.split(" - ", 1)
                        platform_name = parts[0].strip()
                        contest_name = parts[1].strip()
                    else:
                        platform_name = group
                        contest_name = "problem"
                    group_dir = slugify(platform_name)
                    contestname_dir = slugify(contest_name)
                    name_file = slugify(name)
                    cpp_output_dir = os.path.join(special_base_dir, group_dir, contestname_dir)
                    filename_base = name_file
                    test_output_dir = os.path.join(special_base_dir, group_dir, contestname_dir)

                cpp_path = path.join(cpp_output_dir, "{}.cpp".format(filename_base))
                os.makedirs(cpp_output_dir, exist_ok=True)

                # 写入 cpp 文件
                if not path.exists(cpp_path):
                    template_content = make_cpp_template(
                        name=name,
                        url=url,
                        contestname=contestname,
                        time_limit=time_limit,
                        memory_limit=memory_limit,
                        group=group
                    )
                    with open(cpp_path, "w", encoding="utf8") as f:
                        f.write(template_content)

                # 设置项目根目录为 D:\wqnd\Desktop\ACM
                project_data = sublime.active_window().project_data() or {}
                folders = project_data.get("folders", [])
                if not any(f.get("path", "") == r"D:\\wqnd\\Desktop\\ACM" for f in folders):
                    project_data["folders"] = [{"path": r"D:\\wqnd\\Desktop\\ACM"}]
                    sublime.active_window().set_project_data(project_data)

                # 写入测试数据，文件名为 cpp文件名+__tests
                test_filename = "{}__tests".format(path.basename(cpp_path))
                test_path = path.join(cpp_output_dir, test_filename)
                formatted_tests = []
                for test in tests:
                    formatted_tests.append({
                        "test": test["input"],
                        "correct_answers": [test["output"].strip()]
                    })
                with open(test_path, "w", encoding="utf8") as f:
                    f.write(json.dumps(formatted_tests, indent=2))

                # 打开 cpp 文件并展开到侧边栏
                view = sublime.active_window().open_file(cpp_path)
                sublime.active_window().run_command("reveal_in_side_bar")
                print("[Hook] Created: {}".format(cpp_path))
                print("[Hook] Test cases: {}".format(test_path))
            except Exception as e:
                print("[Hook] Error:", e)
                traceback.print_exc()  # 打印完整报错堆栈

    return HandleRequests

class CompetitiveCompanionServer:
    def startServer(foc_settings):
        host = 'localhost'
        port = 12345
        HandlerClass = MakeHandlerClass(foc_settings)
        try:
            httpd = HTTPServer((host, port), HandlerClass)
            print("[Hook] Listening on {}:{} ...".format(host, port))
            httpd.serve_forever()
        except OSError as e:
            print("[Hook] Port {} in use or failed: {}".format(port, e))

def plugin_loaded():
    try:
        foc_settings = sublime.load_settings("FastOlympicCoding.sublime-settings")
        _thread.start_new_thread(
            CompetitiveCompanionServer.startServer,
            (foc_settings,)
        )
        print("[Hook] Auto-listening for Competitive Companion...")
    except Exception as e:
        print("[Hook] Auto-startup error:", e)
