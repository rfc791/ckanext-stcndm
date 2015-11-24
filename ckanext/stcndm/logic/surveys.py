#!/usr/bin/env python
# encoding: utf-8
import ckanapi
from ckan.logic import get_or_bust, side_effect_free, NotFound, ValidationError
import json


@side_effect_free
def get_survey_codesets(context, data_dict):
    """
    Returns all survey codesets.

    :param limit: Number of results to return.
    :type limit: int
    :param start: Number of results to skip.
    :type start: int

    :rtype: list of dicts
    """
    lc = ckanapi.LocalCKAN(context=context)

    # Sort would perform better, but this will be easier
    # for client to implement.
    limit = int(get_or_bust(data_dict, 'limit'))
    start = int(get_or_bust(data_dict, 'start'))

    results = lc.action.package_search(
        q='dataset_type:survey',
        rows=limit,
        start=start,
        sort='survey_code asc',
        fl=(
            'name',
            'title'
        )
    )

    return {
        'count': results['count'],
        'limit': limit,
        'start': start,
        'results': [{
            'survey_code': r['product_id_new'],
            'title': r['title'],
        } for r in results['results']]
    }


def register_survey(context, data_dict):
    """
    Registers a new survey, then tags it with given subject codes.

    :param productId: Product ID of new survey
    :type productId: str
    :param subjectCodes: (optional) List of subject codes
    :type subjectCodes: list of str
    :param titleEn: (optional) English title
    :type titleEn: str
    :param titleFr: (optional) French title
    :type titleFr: str

    :return: new package
    :rtype: dict

    :raises: ValidationError
    """

    product_id = get_or_bust(data_dict, 'productId')
    subject_codes = data_dict.get('subjectCodes', [])
    if not isinstance(subject_codes, list):
        try:
            subject_codes = json.loads(subject_codes)
        except (TypeError, ValueError) as e:
            raise ValidationError(e)
    title_en = data_dict.get('titleEn', 'title for survey-'+product_id)
    title_fr = data_dict.get('titleFr', 'titre pour survey-'+product_id)
    lc = ckanapi.LocalCKAN(context=context)
    new_package = lc.action.package_create(
        **{
            u'owner_org': u'statcan',
            u'private': False,
            u'name': u'survey-{0}'.format(product_id),
            u'type': u'survey',
            u'title': {
                u'en': title_en,
                u'fr': title_fr
            },
            u'product_id_new': product_id,
            u'subject_codes': subject_codes
        }
    )
    return new_package


def get_survey_subject_codes(context, data_dict):
    """
    Returns the list of subject codes tagged to given survey

    :param productId: Product ID of survey
    :type productId: str

    :return: subject codes
    :rtype: list of str
    """

    product_id = get_or_bust(data_dict, 'productId')
    lc = ckanapi.LocalCKAN(context=context)
    results = lc.action.package_search(
        q='name:survey-{product_id}'.format(product_id=product_id)
    )
    if results['count'] < 1:
        raise NotFound(('{product_id}: Survey not found'
                        .format(product_id=product_id),))

    return json.dumps(results['results'][0].get('subject_codes', []))
