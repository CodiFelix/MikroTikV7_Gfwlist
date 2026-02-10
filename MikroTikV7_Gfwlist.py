import base64
import re
import tldextract
from datetime import datetime
import os
import urllib.request

def download_gfwlist():
    """下载 GFWList 源文件"""
    url = 'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt'
    output_file = 'base64.txt'
    
    try:
        print(f'正在下载最新的 GFWList 源文件...')
        urllib.request.urlretrieve(url, output_file)
        print(f'下载完成: {output_file}')
    except Exception as e:
        print(f'下载失败: {e}')
        print('请手动下载或使用以下命令:')
        print(f'wget -O {output_file} {url}')
        exit(1)

def is_valid_domain(domain):
    # 只保留 ASCII 字母、数字、- 和点，且不以-开头结尾，且至少一部分包含字母
    if len(domain) > 253:
        return False
    # 排除包含特殊字符的域名
    invalid_chars = ['[', ']', '*', '?', '<', '>', '"', "'", '|', '\\', ' ']
    if any(char in domain for char in invalid_chars):
        return False
    if re.match(r'^[a-zA-Z0-9.-]+$', domain) is None:
        return False
    if domain.startswith('-') or domain.endswith('-'):
        return False
    if '.' not in domain:
        return False
    # 最后部分至少有两个字母
    if len(domain.split('.')[-1]) < 2:
        return False
    # 任意一段必须含字母
    if not any(c.isalpha() for c in domain.replace('.', '')):
        return False
    return True

def extract_domains_from_gfwlist(file_path):
    # 1. 读取并解码
    with open(file_path, 'rb') as f:
        b64data = f.read()
    content = base64.b64decode(b64data).decode(errors="ignore")

    domains = set()

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith('!') or line.startswith('[') or line.startswith('@'):
            continue
        # 用正则抽取域名
        candidates = re.findall(r'([a-zA-Z0-9.-]+\.[a-zA-Z]+)', line)
        for c in candidates:
            if is_valid_domain(c):
                ext = tldextract.extract(c)
                if ext.domain and ext.suffix:
                    sld = ext.domain + '.' + ext.suffix
                    if is_valid_domain(sld):
                        domains.add(sld.lower())
    return sorted(domains)

if __name__ == '__main__':
    # 下载 GFWList 源文件（如果不存在）
    download_gfwlist()
    
    result = extract_domains_from_gfwlist('base64.txt')
    
    # 生成域名列表文件
    with open('gfwlist_sld.txt', 'w') as out:
        for d in result:
            out.write(d + '\n')
    
    # 生成RouterOS脚本文件
    with open('gfwlist7_domain.rsc', 'w', encoding='utf-8') as rsc:
        create_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        rsc.write(f'### --- 创建时间: {create_time} --- ###\n')
        rsc.write(f':log info "开始更新GFWLIST域名规则..."\n')
        rsc.write('/ip dns static remove [find comment=Gfwlist]\n')
        rsc.write('/ip dns static\n')
        for d in result:
            rsc.write(f':do {{ add comment=Gfwlist type=FWD forward-to=8.8.8.8 match-subdomain=yes name={d} }} on-error={{}}\n')
        rsc.write(':delay 5s;\n')
        rsc.write('/ip dns cache flush\n')
        rsc.write(':log info "完成更新GFWLIST域名规则."\n')
    print(f'成功处理 {len(result)} 个域名')
    print('生成文件: gfwlist_sld.txt, gfwlist7_domain.rsc')
    print(f'Extracted {len(result)} second-level domains. Saved to gfwlist_sld.txt')
