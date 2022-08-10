#!/usr/bin/env/python
# vim: tabstop=4 shiftwidth=4 softtabstop=4 noexpandtab:
# --------------------------------------------------------------------
# (C) Copyright 2018-2019 Red Hat, Inc.
#
# Author: Daniel Sungju Kwon <dkwon@redhat.com>
#
# This command 'pstree' shows process list in tree format
#
#
# Contributors:
# --------------------------------------------------------------------
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
from pykdump.API import *

from LinuxDump.Tasks import (Task, TaskTable, getTaskState,
     task_state_color, task_state_str)
from LinuxDump import crashcolor

import sys

class LineType(object):
    LINE_SPACE = 0,
    LINE_FIRST = 1,
    LINE_BRANCH = 2,
    LINE_LAST = 3,
    LINE_VERT = 4


line_type = ["    ", "-+- ", " |- ", " `- ", " |  "]
pid_cnt = 0
branch_bar = []
branch_locations = []


def findTaskByPid(task_id):
    init_task = readSymbol("init_task")
    for task in readSUListFromHead(init_task.tasks,
                                   "tasks",
                                   "struct task_struct",
                                   maxel=1000000):
        if (task.pid == task_id or task.tgid == task_id):
            return task

def print_pstree(options):
    global pid_cnt
    pid_cnt = 0
    init_task = readSymbol("init_task")
    if (options.task_id > 0):
        tt = TaskTable()
        init_task = tt.getByPid(options.task_id)
        if (init_task == None):
            init_task = findTaskByPid(options.task_id)
        if (init_task == None):
            return

    print_task(init_task, 0, True, options)
    print_children(init_task, 0, options)

    print ("\n\nTotal %s tasks printed" % (pid_cnt))

def print_branch(depth, first):
    global branch_locations
    global branch_bar

    if (first and depth > 0):
        print ("%s" % (line_type[1]), end='')
        return

    for i in range(0, depth):
        for j in range (0, branch_locations[i]):
            print (" ", end='')

        k = branch_bar[i]
        if (type(k) == tuple):
            k = k[0]
#        print ("b = %d, k = %d" % (branch_locations[i], k), end='')
        print("%s" % (line_type[k]), end='')

def get_thread_count(task):
    thread_list = readSUListFromHead(task.thread_group,
                                     'thread_group',
                                     'struct task_struct',
                                     maxel=1000000);
    return len(thread_list)

def print_task(task, depth, first, options):
    global pid_cnt
    global branch_locations

    if (task == None):
        return

    pid_cnt = pid_cnt + 1
    thread_str = ""
    if (options.print_thread):
        thread_count = get_thread_count(task)
        if (thread_count > 1):
            if (task.tgid == task.pid):
                thread_str = "---%d*[{%s}]" % (thread_count, task.comm)
            else:
                return 0

    print_branch(depth, first)

    comm_str = ""
    if (task.comm != 0):
        comm_str = task.comm

    state = getTaskState(task)
    task_color = task_state_color(state)
    if task_color != crashcolor.RESET:
        crashcolor.set_color(task_color)

    print_str = ("%s%s%s%s " %
           (comm_str,
            "(" + str(task.pid) + ")"
                if options.print_pid else "",
            "[" + task_state_str(state) +"]"
                if options.print_state else "",
            thread_str))
    print ("%s" % (print_str), end='')
    if task_color != crashcolor.RESET:
        crashcolor.set_color(crashcolor.RESET)
    if (len(branch_locations) <= depth):
        branch_locations.append(len(print_str))
    else:
        branch_locations[depth] = len(print_str)

    return 1


def print_children(task, depth, options):
    global branch_bar

    if (task == None):
        return

    depth = depth + 1
    while (len(branch_bar) <= depth):
        branch_bar.append(LineType.LINE_SPACE)

    first = True
    child_list = readSUListFromHead(task.children,
                                    'sibling',
                                    'struct task_struct',
                                    maxel=1000000)
    for idx, child in enumerate(child_list):
        if (idx == len(child_list) - 1):
            branch_bar[depth - 1] = LineType.LINE_LAST
        else:
            branch_bar[depth - 1] = LineType.LINE_BRANCH

        printed = print_task(child, depth, first, options)
        first = False

        if (idx == len(child_list) - 1):
            branch_bar[depth - 1] = LineType.LINE_SPACE
        else:
            branch_bar[depth - 1] = LineType.LINE_VERT

        print_children(child, depth, options)

        if (idx != len(child_list) - 1):
            if (printed > 0):
                print()

def pstree():
    op = OptionParser()
    op.add_option("-p", dest="print_pid", default=0,
                  action="store_true",
                  help="Print process ID")
    op.add_option("-g", dest="print_thread", default=0,
                  action="store_true",
                  help="Print number of threads")
    op.add_option("-s", dest="print_state", default=0,
                  action="store_true",
                  help="Print task state")
    op.add_option("-t", dest="task_id", default=0,
                  type="int", action="store",
                  help="Print specific task and its children")

    (o, args) = op.parse_args()

    print_pstree(o)


if ( __name__ == '__main__'):
    pstree()
