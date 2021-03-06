#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (C) 2019 tribe29 GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""Mode for trying out the logwatch patterns"""

import re

import six

from cmk.utils.type_defs import CheckPluginName, HostName, ServiceName, Item  # pylint: disable=unused-import

import cmk.gui.watolib as watolib
from cmk.gui.table import table_element
import cmk.gui.forms as forms
from cmk.gui.htmllib import HTML
from cmk.gui.i18n import _
from cmk.gui.globals import html
from cmk.gui.exceptions import MKUserError

from cmk.gui.plugins.wato import (
    WatoMode,
    mode_registry,
    global_buttons,
    ConfigHostname,
)

# Tolerate this for 1.6. Should be cleaned up in future versions,
# e.g. by trying to move the common code to a common place
# import cmk.base.export


@mode_registry.register
class ModePatternEditor(WatoMode):
    @classmethod
    def name(cls):
        return "pattern_editor"

    @classmethod
    def permissions(cls):
        return ["pattern_editor"]

    def _from_vars(self):
        self._hostname = self._vs_host().from_html_vars("host")
        self._vs_host().validate_value(self._hostname, "host")

        # TODO: validate all fields
        self._item = html.request.get_unicode_input_mandatory('file', u'')
        self._match_txt = html.request.get_unicode_input_mandatory('match', u'')

        self._host = watolib.Folder.current().host(self._hostname)

        if self._hostname and not self._host:
            raise MKUserError(None, _("This host does not exist."))

        if self._item and not self._hostname:
            raise MKUserError(None, _("You need to specify a host name to test file matching."))

    def title(self):
        if not self._hostname and not self._item:
            return _("Logfile Pattern Analyzer")
        if not self._hostname:
            return _("Logfile Patterns of Logfile %s on all Hosts") % (self._item)
        if not self._item:
            return _("Logfile Patterns of Host %s") % (self._hostname)
        return _("Logfile Patterns of Logfile %s on Host %s") % (self._item, self._hostname)

    def buttons(self):
        global_buttons()
        if self._host:
            if self._item:
                title = _("Show Logfile")
            else:
                title = _("Host Logfiles")

            html.context_button(
                title,
                html.makeuri_contextless([("host", self._hostname), ("file", self._item)],
                                         filename="logwatch.py"), 'logwatch')

        html.context_button(
            _('Edit Logfile Rules'),
            watolib.folder_preserving_link([
                ('mode', 'edit_ruleset'),
                ('varname', 'logwatch_rules'),
            ]), 'edit')

    def page(self):
        html.help(
            _('On this page you can test the defined logfile patterns against a custom text, '
              'for example a line from a logfile. Using this dialog it is possible to analyze '
              'and debug your whole set of logfile patterns.'))

        self._show_try_form()
        self._show_patterns()

    def _show_try_form(self):
        html.begin_form('try')
        forms.header(_('Try Pattern Match'))
        forms.section(_('Hostname'))
        self._vs_host().render_input("host", self._hostname)
        forms.section(_('Logfile'))
        html.text_input('file')
        forms.section(_('Text to match'))
        html.help(
            _('You can insert some text (e.g. a line of the logfile) to test the patterns defined '
              'for this logfile. All patterns for this logfile are listed below. Matching patterns '
              'will be highlighted after clicking the "Try out" button.'))
        html.text_input('match', cssclass='match', size=100)
        forms.end()
        html.button('_try', _('Try out'))
        html.request.del_var('folder')  # Never hand over the folder here
        html.hidden_fields()
        html.end_form()

    def _vs_host(self):
        return ConfigHostname()

    def _show_patterns(self):
        import cmk.gui.logwatch as logwatch
        collection = watolib.SingleRulesetRecursively("logwatch_rules")
        collection.load()
        ruleset = collection.get("logwatch_rules")

        html.h3(_('Logfile Patterns'))
        if ruleset.is_empty():
            html.open_div(class_="info")
            html.write_text('There are no logfile patterns defined. You may create '
                            'logfile patterns using the <a href="%s">Rule Editor</a>.' %
                            watolib.folder_preserving_link([
                                ('mode', 'edit_ruleset'),
                                ('varname', 'logwatch_rules'),
                            ]))
            html.close_div()

        # Loop all rules for this ruleset
        already_matched = False
        abs_rulenr = 0
        for folder, rulenr, rule in ruleset.get_rules():
            # Check if this rule applies to the given host/service
            if self._hostname:
                service_desc = self._get_service_description(self._hostname, "logwatch", self._item)

                # If hostname (and maybe filename) try match it
                rule_matches = rule.matches_host_and_item(watolib.Folder.current(), self._hostname,
                                                          self._item, service_desc)
            else:
                # If no host/file given match all rules
                rule_matches = True

            html.begin_foldable_container("rule",
                                          "%s" % abs_rulenr,
                                          True,
                                          HTML("<b>Rule #%d</b>" % (abs_rulenr + 1)),
                                          indent=False)
            with table_element("pattern_editor_rule_%d" % abs_rulenr, sortable=False) as table:
                abs_rulenr += 1

                # TODO: What's this?
                pattern_list = rule.value
                if isinstance(pattern_list, dict):
                    pattern_list = pattern_list["reclassify_patterns"]

                # Each rule can hold no, one or several patterns. Loop them all here
                for state, pattern, comment in pattern_list:
                    match_class = ''
                    disp_match_txt = HTML('')
                    match_img = ''
                    if rule_matches:
                        # Applies to the given host/service
                        reason_class = 'reason'

                        matched = re.search(pattern, self._match_txt)
                        if matched:

                            # Prepare highlighted search txt
                            match_start = matched.start()
                            match_end = matched.end()
                            disp_match_txt = html.render_text(self._match_txt[:match_start]) \
                                             + html.render_span(self._match_txt[match_start:match_end], class_="match")\
                                             + html.render_text(self._match_txt[match_end:])

                            if not already_matched:
                                # First match
                                match_class = 'match first'
                                match_img = 'match'
                                match_title = _(
                                    'This logfile pattern matches first and will be used for '
                                    'defining the state of the given line.')
                                already_matched = True
                            else:
                                # subsequent match
                                match_class = 'match'
                                match_img = 'imatch'
                                match_title = _(
                                    'This logfile pattern matches but another matched first.')
                        else:
                            match_img = 'nmatch'
                            match_title = _('This logfile pattern does not match the given string.')
                    else:
                        # rule does not match
                        reason_class = 'noreason'
                        match_img = 'nmatch'
                        match_title = _('The rule conditions do not match.')

                    table.row(css=reason_class)
                    table.cell(_('Match'))
                    html.icon(match_title, "rule%s" % match_img)

                    cls = ''
                    if match_class == 'match first':
                        cls = 'svcstate state%d' % logwatch.level_state(state)
                    table.cell(_('State'), logwatch.level_name(state), css=cls)
                    table.cell(_('Pattern'), html.render_tt(pattern))
                    table.cell(_('Comment'), html.render_text(comment))
                    table.cell(_('Matched line'), disp_match_txt)

                table.row(fixed=True)
                table.cell(colspan=5)
                edit_url = watolib.folder_preserving_link([
                    ("mode", "edit_rule"),
                    ("varname", "logwatch_rules"),
                    ("rulenr", rulenr),
                    ("host", self._hostname),
                    ("item", six.ensure_str(watolib.mk_repr(self._item))),
                    ("rule_folder", folder.path()),
                ])
                html.icon_button(edit_url, _("Edit this rule"), "edit")

            html.end_foldable_container()

    def _get_service_description(self, hostname, check_plugin_name, item):
        # type: (HostName, CheckPluginName, Item) -> ServiceName
        # TODO: re-enable once the GUI is using Python3
        #return cmk.base.export.service_description(hostname, check_plugin_name, item)
        assert item is not None
        return watolib.check_mk_local_automation("get-service-name",
                                                 [hostname, check_plugin_name, item])
