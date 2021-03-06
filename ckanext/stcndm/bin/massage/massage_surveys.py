import sys
import json
import yaml
import ckanapi
from datetime import datetime
from dateutil.parser import parse
from dateutil.tz import gettz
import inspect
import os

__author__ = 'marc'


path = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
default_date = datetime(1, 1, 1, 0, 0, 0, 0, tzinfo=gettz('America/Toronto'))
default_release_date = datetime(1, 1, 1, 8, 30, 0, 0,
                                tzinfo=gettz('America/Toronto'))


def to_utc(date_str, def_date=default_date):
    result = parse(date_str, default=def_date)
    utc_result = result.astimezone(gettz('UTC'))
    return utc_result.replace(tzinfo=None).isoformat()


def listify(value):
    if isinstance(value, unicode):
        # filter removes empty strings
        return filter(None, map(unicode.strip, value.split(';')))
    elif isinstance(value, list):
        return filter(None, map(unicode.strip, value[0].split(';')))
    else:
        return []


def code_lookup(old_field_name, data_set, choice_list):
    _temp = data_set[old_field_name]
    field_values = listify(_temp)
    codes = []
    for field_value in field_values:
        code = None
        for choice in choice_list:
            if choice['label']['en'].lower() == field_value.lower():
                if choice['value']:
                    code = choice['value']
        if not code:
            sys.stderr.write(
                'survey-{product_id}: unrecognized {field_name}: '
                '.{field_value}.\n'.format(
                    product_id=line.get(u'productidnew_bi_strs', u'product_id'),
                    field_name=old_field_name,
                    field_value=field_value
                )
            )
        else:
            codes.append(code)
    return codes


def safe_get(my_list):
    if len(my_list):
        return my_list[0]
    return ''

content_type_list = []
rc = ckanapi.RemoteCKAN('http://127.0.0.1:5000')
results = rc.action.package_search(
    q='type:codeset',
    rows=1000)

raw_codesets = results['results']
for codeset in raw_codesets:
    if codeset['codeset_type'] == 'content_type':
        content_type_list.append({
            'label': codeset['title'],
            'value': codeset['codeset_value']
        })

f = open(path+'/../../schemas/presets.yaml')
presetMap = yaml.safe_load(f)
f.close()

archive_status_list = []
collection_method_list = []
survey_status_list = []
survey_participation_list = []
survey_owner_list = []

for preset in presetMap['presets']:
    if preset['preset_name'] == 'ndm_archive_status':
        archive_status_list = preset['values']['choices']
        if not archive_status_list:
            raise ValueError('could not find archive status preset')
    if preset['preset_name'] == 'ndm_collection_methods':
        collection_method_list = preset['values']['choices']
        if not collection_method_list:
            raise ValueError('could not find collection method preset')
    if preset['preset_name'] == 'ndm_survey_status':
        survey_status_list = preset['values']['choices']
        if not survey_status_list:
            raise ValueError('could not find survey status preset')
    if preset['preset_name'] == 'ndm_survey_participation':
        survey_participation_list = preset['values']['choices']
        if not survey_participation_list:
            raise ValueError('could not find survey participation preset')
    if preset['preset_name'] == 'ndm_survey_owner':
        survey_owner_list = preset['values']['choices']
        if not survey_owner_list:
            raise ValueError('could not find survey owner preset')
#    if preset['preset_name'] == 'ndm_format':
#        format_list = preset['values']['choices']
#        if not format_list:
#            raise ValueError('could not find format preset')

deleted_subject_codes = [
    '130901',
    '140206',
    '2101',
    '26',
    '2602',
    '2603',
    '2606',
    '2699',
    '3103',
    '3404',
    '3451',
    '3452',
    '350301',
    '3507',
    '3706',
    '3710',
    '380401',
    '4302',
    '4304',
    '4307',
    '673901',
    '675178'
]

rc = ckanapi.RemoteCKAN('http://ndmckanq1.stcpaz.statcan.gc.ca/zj/')
i = 0
n = 1
while i < n:
    query_results = rc.action.package_search(
        q='organization:maimdb',
        rows=1000,
        start=i*1000)
    i += 1
    n = query_results['count'] / 1000.0

    for line in query_results[u'results']:
        for e in line[u'extras']:
            line[e[u'key']] = e[u'value']

        line_out = {
            u'owner_org': u'statcan',
            u'private': False,
            u'type': u'survey',
            u'archive_status_code': safe_get(
                code_lookup(u'archived_bi_strs', line, archive_status_list)),
            u'content_type_codes': u'2003',
            u'collection_method_codes': code_lookup(
                u'collmethod_en_txtm', line, collection_method_list),
            u'notes': {
                u'en': line.get(u'description_en_txts', ''),
                u'fr': line.get(u'description_fr_txts', '')
            },
            u'feature_weight': line.get(u'featureweight_bi_ints', ''),
            u'frc': line.get(u'frccode_bi_strs', ''),
            u'frequency_codes': listify(line.get(u'freqcode_bi_txtm', '')),
            u'keywords': {
                u'en': listify(line.get(u'keywordsuncon_en_txtm', '')),
                u'fr': listify(line.get(u'keywordsuncon_fr_txtm', ''))
            },
            u'survey_instance_item': line.get(u'imdbinstanceitem_bi_ints', ''),
            u'survey_item': line.get(u'imdbsurveyitem_bi_ints', ''),
            u'isp_url': {
                u'en': line.get(u'isplink_en_strs', ''),
                u'fr': line.get(u'isplink_fr_strs', '')
            },
            u'level_subject_codes': listify(
                line.get(u'extras_levelsubjcode_bi_txtm', '')),
            u'product_id_new': line.get(u'productidnew_bi_strs', ''),
            u'name': u'survey-{0}'.format(
                line.get(u'productidnew_bi_strs', '')),
            u'question_url': {
                u'en': line.get(u'questlink_en_strs', ''),
                u'fr': line.get(u'questlink_fr_strs', ''),
            },
            u'reference_period': {
                u'en': line.get(u'refperiod_en_txtm', u''),
                u'fr': line.get(u'refperiod_fr_txtm', u''),
            },
            u'thesaurus_terms': {
                u'en': listify(line.get(u'stcthesaurus_en_txtm', '')),
                u'fr': listify(line.get(u'stcthesaurus_fr_txtm', '')),
            },
            u'survey_status_code': safe_get(
                code_lookup(u'statusf_en_strs', line, survey_status_list)),
            u'subject_codes': listify(line.get(u'subjnewcode_bi_txtm', '')),
            u'survey_url': {
                u'en': line.get(u'surveylink_en_strs', ''),
                u'fr': line.get(u'surveylink_fr_strs', '')
            },
            u'survey_participation_code': safe_get(
                code_lookup(
                    u'surveyparticipation_en_strs',
                    line,
                    survey_participation_list)),
            u'survey_owner_code': safe_get(
                code_lookup(u'survowner_en_strs', line, survey_owner_list)),
            u'title': {
               u'en': line.get(u'title_en_txts', ''),
               u'fr': line.get(u'title_fr_txts', '')
            },
            u'url': {
                u'en': line.get(u'url_en_strs', ''),
                u'fr': line.get(u'url_fr_strs', '')
            },
            u'license_title': line.get(u'license_title', ''),
            u'license_url': line.get(u'license_url', ''),
            u'license_id': line.get(u'license_id', '')
        }
        for code in deleted_subject_codes:
            if code in line_out[u'subject_codes']:
                line_out[u'subject_codes'].remove(code)

        if u'collenddate_bi_strs' in line and line[u'collenddate_bi_strs']:
            line_out[u'collection_end_date'] = to_utc(
                line.get(u'collenddate_bi_strs'),
                default_date)

        if u'collstartdate_bi_strs' in line and line[u'collstartdate_bi_strs']:
            line_out[u'collection_start_date'] = to_utc(
                line.get(u'collstartdate_bi_strs'),
                default_date)

        if u'releasedate_bi_strs' in line and line[u'releasedate_bi_strs']:
            line_out[u'last_release_date'] = to_utc(
                line.get(u'releasedate_bi_strs'),
                default_release_date)

        print json.dumps(line_out)
