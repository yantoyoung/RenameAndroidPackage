#!/usr/bin/env python
# -*- coding: utf-8 -*-
#author:lijunjie
#email:lijunjieone@gmail.com

import codecs
import os
import re
import sys
import xml.dom.minidom as minidom

from optparse import OptionParser
from xml.etree import ElementTree as ET


class Project:
    def __init__(self):
        pass


class RenameAndroidPackage:
    def __init__(self, p):
        self.project = p

    def modify_android_manifest(self):
        mod_manifest = ModAndroidManifest("%s/AndroidManifest.xml" % self.project.build_path)
        self.project.old_package_name = mod_manifest.get_old_package_name()
        mod_manifest.rename_package_name(self.project.new_package_name)
        mod_manifest.save_xml()

    def modify_source(self,old_package_name):
        source_path="%s/src/"%(self.project.build_path)
        package_name_path=old_package_name.replace(".","/")
        for a,b,c in os.walk(source_path):
            if ".svn" not in a:
                for i in c:
                    file_path="%s/%s"%(a,i)
                    if ".java" in i and a.endswith(package_name_path):
                        replace_string(file_path,"%s;"%(old_package_name),"%s;\nimport %s.R;"%(old_package_name,self.project.new_package_name))
                        replace_string(file_path,"%s;"%(old_package_name),"%s;\nimport %s.BuildConfig;"%(old_package_name,self.project.new_package_name))
                    elif ".java" in i:
                        replace_string(file_path,"%s.R"%old_package_name,"%s.R"%self.project.new_package_name)
                        replace_string(file_path,"%s.BuildConfig"%old_package_name,"%s.BuildConfig"%self.project.new_package_name)

    def modify_resource(self,old_package_name):
        res_path="%s/res/"%(self.project.build_path)
        for a,b,c in os.walk(res_path):
            if ".svn" not in a:
                for i in c:
                    if "strings.xml" in i:
                        xml_path = os.path.join(a, i)
                        root = ET.parse(xml_path).getroot()
                        for elem in root:
                            if "app_name" in elem.attrib["name"]:
                                if "dev" in self.project.new_package_name:
                                    replace_string(xml_path, elem.text, elem.text+"Dev")
                                elif "uat" in self.project.new_package_name:
                                    replace_string(xml_path, elem.text, elem.text+"UAT")
                    elif ".xml" in i:
                        file_path="%s/%s"%(a,i)
                        replace_string(file_path,"http://schemas.android.com/apk/res/%s"%old_package_name,"http://schemas.android.com/apk/res/%s"%self.project.new_package_name)

    def modify(self):
        self.modify_android_manifest()
        self.modify_source(self.project.old_package_name)
        self.modify_resource(self.project.old_package_name)


class ModAndroidManifest:
    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.root = ET.parse(xml_path).getroot()
        self.ns_android = "http://schemas.android.com/apk/res/android"
        ET._namespace_map["http://schemas.android.com/apk/res/android"] = "android"

    def get_old_package_name(self):
        return self.root.attrib["package"]

    def rename_package_name(self, new_package):
        self.old_package = self.root.attrib["package"]
        self.new_package = new_package
        self.root.attrib["package"] = self.new_package

        for i in self.root:
            if i.tag == "application":
                app = i
                break

        # Loop through the sub-elements for tag "application"
        for i in app:
            # Look for attrib "android:name". If its value starts with "."
            # as in the case of Activity, then rename it to its full package name
            # e.g. ".ui.MainActivity" to "com.example.ui.MainActivity"
            android_name_attrib = i.attrib["{%s}name" % self.ns_android]
            if android_name_attrib.startswith("."):
                x = "%s%s" % (self.old_package, android_name_attrib)
                i.attrib["{%s}name" % self.ns_android] = x
            # Look for attrib "android:authorities" in tag "provider",
            # and rename the value to correspond to the new package name.
            if i.tag == "provider":
                i.attrib["{%s}authorities" % self.ns_android] = i.attrib["{%s}authorities" % self.ns_android].replace(self.old_package, self.new_package)
        
    def format_xml(self):
        rough_string = ET.tostring(self.root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        self.content = reparsed.toprettyxml(indent=' ', encoding='utf-8')
        return self.content

    def save_xml(self):
        self.format_xml()
        f = codecs.open(self.xml_path, "w", "utf-8")
        content2 = ""
        for i in self.content.split("\n"):
            if i.strip() != '':
                content2 += i
                content2 += "\n"
        f.write(content2)
        f.close()


def replace_string(filename,src_text,dest_text):
    print filename, src_text.encode("ascii", "ignore"), dest_text.encode("ascii", "ignore")
    src = u'%s' % src_text
    dest = u'%s' % dest_text

    aa = codecs.open(filename, "r", "utf-8")
    a = aa.read()
    aa.close()

    b = re.sub(src, dest, a)
    c = codecs.open(filename, "w", "utf-8")
    c.write(b)
    c.close()


def handle_params(fakeArgs):
    msg_usage = "%prog [ -p <project_path> ] [ -o <old_name> ] [ -n <new_name> ]"

    optParser = OptionParser(msg_usage)
    optParser.add_option("-p", "--project_path", action="store", type="string", dest="project_path")
    optParser.add_option("-o", "--old_package_name", action="store", type="string", dest="old_package_name")
    optParser.add_option("-n", "--new_package_name", action="store", type="string", dest="new_package_name")

    return optParser.parse_args(fakeArgs)
 

if __name__ == "__main__":

    arg = sys.argv[1:]
    if len(arg) == 0:
        arg.append("--help")

    options, args = handle_params(arg) 

    p = Project()
    p.build_path = options.project_path
    p.old_package_name = options.old_package_name
    p.new_package_name = options.new_package_name

    r = RenameAndroidPackage(p)
    r.modify()
