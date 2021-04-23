#!/usr/bin/env fish

set BASE ../../../march-2021/

rm -rf content
mkdir -p content
cp -r $BASE content/

for i in (find content/ -iname "*.md")
    echo "relinking '$i'"
    awk -i inplace -e '{ print gensub(/\(([^/]\S+)\)/,"(../\\\\1)","g",$0); }' "$i"
    awk -i inplace -e '{ print gensub(/\(([^/]\S+)#(.*)\)/,"(../\\\\1#\\\\2)","g",$0); }' "$i"
end

for i in (find content/ -iname "*.svg")
    echo "relinking '$i'"
    awk -i inplace -e '{ print gensub(/href=\"([^/]\S+)\.md\"/,"href=\"../\\\\1\"","g",$0); }' "$i"
    awk -i inplace -e '{ print gensub(/href=\"([^/]\S+)\.md#(\S*)\"/,"href=\"../\\\\1#\\\\2\"","g",$0); }' "$i"
end

for i in (find content/ -iname "*.html")
    echo "relinking '$i'"
    awk -i inplace -e '{ print gensub(/href=\"([^/]\S+)\"/,"href=\"../\\\\1\"","g",$0); }' "$i"
    awk -i inplace -e '{ print gensub(/src=\"([^/]\S+)\"/,"src=\"../\\\\1\"","g",$0); }' "$i"
end
