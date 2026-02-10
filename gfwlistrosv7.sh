#!/bin/bash
if [[ $(/usr/bin/id -u) -ne 0 ]]; then
  sudoCmd="sudo"
else
  sudoCmd=""
fi
#copy from ITinflect-Ctrl scripts
if [[ -f /etc/redhat-release ]]; then
  release="centos"
  systemPackage="yum"
elif cat /etc/issue | grep -Eqi "debian"; then
  release="debian"
  systemPackage="apt-get"
elif cat /etc/issue | grep -Eqi "ubuntu"; then
  release="ubuntu"
  systemPackage="apt-get"
elif cat /etc/issue | grep -Eqi "centos|red hat|redhat"; then
  release="centos"
  systemPackage="yum"
elif cat /proc/version | grep -Eqi "debian"; then
  release="debian"
  systemPackage="apt-get"
elif cat /proc/version | grep -Eqi "ubuntu"; then
  release="ubuntu"
  systemPackage="apt-get"
elif cat /proc/version | grep -Eqi "centos|red hat|redhat"; then
  release="centos"
  systemPackage="yum"
fi
if [ ${systemPackage} == "yum" ]; then
    ${sudoCmd} ${systemPackage} install wget -y -q
else
    ${sudoCmd} ${systemPackage} install wget -y -qq
fi

if [ ${release} == "centos" ]; then
    nginx_root="/usr/share/nginx/html"
else
    nginx_root="/var/www/html"
fi
wget -O base64.txt https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt > /dev/null 2>&1
gfwlist_domain_filename="./Result/gfwlist7_domain.rsc"
gfwlist_source_domain_filename="./Result/gfwlist7_domain_source.rsc"
chmod +x gfwlistdnsmasq.sh && sh ./gfwlistdnsmasq.sh -l -o ${gfwlist_domain_filename}
cp ${gfwlist_domain_filename} ${gfwlist_source_domain_filename}

# 增加额外需要加入gfwlist的域名
echo "libreswan.org" >> ${gfwlist_domain_filename}
echo "i.ytimg.com" >> ${gfwlist_domain_filename}
echo "download.mikrotik.com" >> ${gfwlist_domain_filename}

# RouterOS v7 gfwlist scripts
sed -i 's/^/:do { add comment=Gfwlist type=FWD forward-to=8.8.8.8 match-subdomain=yes name=&/g' ${gfwlist_domain_filename}
sed -i 's/$/&\ } on-error={}/g' ${gfwlist_domain_filename}
sed -i '1 i/log info "Loading MikroTik v7 Gfwlist"' ${gfwlist_domain_filename}
sed -i '2 i/ip dns static/remove [ find comment=Gfwlist ]' ${gfwlist_domain_filename}
sed -i '3 i/ip dns static' ${gfwlist_domain_filename}
sed -i '$a\:delay 3s;' ${gfwlist_domain_filename}
sed -i '$a\/ip dns cache flush' ${gfwlist_domain_filename}
sed -i '$a\:log info "Complete CN_IPv4_ROUTE !!"' ${gfwlist_domain_filename}
echo "Translation completed !!"
