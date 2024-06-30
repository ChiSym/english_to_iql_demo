
export const iql = ({ regex }) => {
  const COMMA = {
    scope: 'punctuation',
    match: /,/,
    relevance: 0,
  };

  const KEYWORDS = [
    'and',
    'asc',
    'by',
    'cross',
    'desc',
    'from',
    'group',
    'inner',
    'join',
    'limit',
    'on',
    'or',
    'order',
    'select',
    'values',
    'where',
  ];

  const BUILT_IN = ['conditioned', 'constrained', 'generate', 'under', 'given'];

  const LITERALS = ['true', 'false', 'NULL'];

  const OPERATORS = ['>', '>=', '=', '<=', '<', /\*/, '/', /\+/, '-'];

  const OPERATOR = {
    scope: 'operator',
    match: regex.either(...OPERATORS),
  };

  const STRING = {
    scope: 'string',
    begin: '"',
    end: '"',
  };

  const VARIABLE = {
    begin: [/VAR/, /\s+/, /[^0-9\s][\w\-_?.]*/],
    beginScope: {
      1: 'built_in',
      3: 'variable',
    },
  };

  const NUMBER = {
    scope: 'number',
    match: /\b-?[0-9]+\.?(?:[0-9]+)?\b/,
  };

  const AGGREGATION_FNS = ['avg', 'count', 'max', 'median', 'min', 'std'];

  const AGGREGATION = {
    scope: 'title.function.invoke',
    match: regex.concat(/\b/, regex.either(...AGGREGATION_FNS), /\s*(?=\()/),
  };

  const SCALAR = {
    begin: regex.concat(/\b/, regex.either('select', 'where'), /\b/),
    excludeBegin: true,
    end: regex.concat(
      /\b/,
      regex.either(
        'asc',
        'desc',
        'from',
        /group\sby/,
        'where',
        /order\sby/,
        'limit'
      ),
      /\b/
    ),
    excludeEnd: true,
    keywords: {
      keyword: ['and', 'distinct', 'as', 'is', 'not', 'or'],
      built_in: [
        'by',
        'conditioned',
        'constrained',
        'density',
        'given',
        'information',
        'mutual',
        'of',
        'probability',
        'under',
        'similar',
        'to',
        'hypothetical',
        'in',
        'context',
      ],
    },
    contains: [AGGREGATION, COMMA, NUMBER, OPERATOR, STRING, VARIABLE],
  };

  return {
    name: 'IQL',
    aliases: ['iql'],
    case_insensitive: true,
    keywords: {
      keyword: KEYWORDS,
      built_in: BUILT_IN,
      literal: LITERALS,
    },
    contains: [COMMA, NUMBER, OPERATOR, STRING, SCALAR],
  };
};
