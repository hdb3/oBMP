
# ref https://www.iana.org/assignments/capability-codes/capability-codes.xml

from capabilitycodes import *
    
class BGP_capability_code_strings:

    BGP_optional_capability_code_strings = {
        1: 'Multiprotocol Extensions for BGP-4',
        2: 'Route Refresh Capability for BGP-4',
        3: 'Outbound Route Filtering',
        4: 'Multiple routes to a destination',
        5: 'Extended Next Hop Encoding',
        6: 'BGP-Extended Message',
        7: 'BGPsec',
        8: 'Multiple Labels',
        9: 'BGP Role',
        64: 'Graceful Restart',
        65: 'Support for 4-octet AS number capability',
        67: 'Support for Dynamic Capability',
        68: 'Multisession BGP',
        69: 'ADD-PATH',
        70: 'Enhanced Route Refresh',
        71: 'Long-Lived Graceful Restart',
        72: 'Unassigned  ',
        73: 'FQDN',
        128: 'Cisco Route refresh'
    }
    
    BGP_optional_capability_code_extended_strings = {
        1: 'Multiprotocol Extensions for BGP-4  [RFC2858]',
        2: 'Route Refresh Capability for BGP-4  [RFC2918]',
        3: 'Outbound Route Filtering Capability [RFC5291]',
        4: 'Multiple routes to a destination capability (deprecated)    [RFC8277]',
        5: 'Extended Next Hop Encoding  [RFC5549]',
        6: 'BGP-Extended Message (TEMPORARY - registered 2015-09-30, extension registered 2017-08-31, expires 2018-09-30)   [draft-ietf-idr-bgp-extended-messages]',
        7: 'BGPsec Capability   [RFC8205]',
        8: 'Multiple Labels Capability  [RFC8277]',
        9: 'BGP Role (TEMPORARY - registered 2018-03-29, expires 2019-03-29)    [draft-ietf-idr-bgp-open-policy]',
        64: 'Graceful Restart Capability [RFC4724]',
        65: 'Support for 4-octet AS number capability    [RFC6793]',
        67: 'Support for Dynamic Capability (capability specific)    [draft-ietf-idr-dynamic-cap]',
        68: 'Multisession BGP Capability [draft-ietf-idr-bgp-multisession]',
        69: 'ADD-PATH Capability [RFC7911]',
        70: 'Enhanced Route Refresh Capability   [RFC7313]',
        71: 'Long-Lived Graceful Restart (LLGR) Capability   [draft-uttaro-idr-bgp-persistence]',
        72: 'Unassigned  ',
        73: 'FQDN Capability [draft-walton-bgp-hostname-capability]',
        128: 'Route refresh capability (Cisco) (128)'
    }
