"""
BI报表参数
"""


def report_field_args(
    report_code: int,
    is_summary: bool = False
):
    """
    BI报表参数
    Args:
        report_code (int): 报表编码
    Returns:
        dict: 报表参数
    """
    if report_code == 63:
        orderFields = [
            {
                "field": "F_3_6555_F",
                "order": None
            },
            {
                "field": "F_3_6557_F",
                "order": None
            },
            {
                "field": "F_3_6556_F",
                "order": None
            },
            {
                "field": "F_3_6560_F",
                "order": None
            },
            {
                "field": "F_3_6561_F",
                "order": None
            },
            {
                "field": "F_3_6562_F",
                "order": None
            },
            {
                "field": "F_3_6564_F",
                "order": None
            },
            {
                "field": "F_3_6563_F",
                "order": None
            },
            {
                "field": "F_3_6576_F",
                "order": None
            },
            {
                "field": "F_3_6601_F",
                "order": None
            },
            {
                "field": "F_3_6610_F",
                "order": None
            },
            {
                "field": "F_3_6613_F",
                "order": None
            },
            {
                "field": "F_3_17843_F",
                "order": None
            },
            {
                "field": "F_3_6602_F",
                "order": None
            },
            {
                "field": "F_3_6567_F",
                "order": None
            },
            {
                "field": "F_3_6568_F",
                "order": None
            },
            {
                "field": "F_3_6575_F",
                "order": None
            },
            {
                "field": "F_3_6584_F",
                "order": None
            }
        ]
        reportFieldIds = [
            "6555",
            "6557",
            "6556",
            "6560",
            "6561",
            "6562",
            "6564",
            "6563",
            "6576",
            "6601",
            "6610",
            "6613",
            "17843",
            "6602",
            "6567",
            "6568",
            "6575",
            "6584"
        ]
    elif report_code == 61:
        orderFields = [
            {
                "field": "F_3_7554_F",
                "order": None
            },
            {
                "field": "F_3_6290_F",
                "order": None
            },
            {
                "field": "F_3_7556_F",
                "order": None
            },
            {
                "field": "F_3_7555_F",
                "order": None
            },
            {
                "field": "F_3_6300_F",
                "order": None
            },
            {
                "field": "F_3_6302_F",
                "order": None
            },
            {
                "field": "F_3_6301_F",
                "order": None
            },
            {
                "field": "F_3_6305_F",
                "order": None
            },
            {
                "field": "F_3_6306_F",
                "order": None
            },
            {
                "field": "F_3_6307_F",
                "order": None
            },
            {
                "field": "F_3_6346_F",
                "order": None
            },
            {
                "field": "F_3_6309_F",
                "order": None
            },
            {
                "field": "F_3_6308_F",
                "order": None
            },
            {
                "field": "F_3_6322_F",
                "order": None
            },
            {
                "field": "F_3_6354_F",
                "order": None
            },
            {
                "field": "F_3_6365_F",
                "order": None
            },
            {
                "field": "F_3_6361_F",
                "order": None
            },
            {
                "field": "F_3_6645_F",
                "order": None
            },
            {
                "field": "F_3_6355_F",
                "order": None
            },
            {
                "field": "F_3_127394_F",
                "order": None
            },
            {
                "field": "F_3_127395_F",
                "order": None
            },
            {
                "field": "F_3_6330_F",
                "order": None
            },
            {
                "field": "F_3_6321_F",
                "order": None
            },
            {
                "field": "F_3_6312_F",
                "order": None
            },
            {
                "field": "F_3_6313_F",
                "order": None
            }
        ]
        reportFieldIds = [
            "7554",
            "6290",
            "7556",
            "7555",
            "6300",
            "6302",
            "6301",
            "6305",
            "6306",
            "6307",
            "6346",
            "6309",
            "6308",
            "6322",
            "6354",
            "6365",
            "6361",
            "6645",
            "6355",
            "127394",
            "127395",
            "6330",
            "6321",
            "6312",
            "6313"
        ]
    elif report_code == 32:
        orderFields = [
            {
                "field": "F_3_4714_F",
                "order": None
            },
            {
                "field": "F_3_4715_F",
                "order": None
            },
            {
                "field": "F_3_4716_F",
                "order": None
            },
            {
                "field": "F_3_4721_F",
                "order": None
            },
            {
                "field": "F_3_33528_F",
                "order": None
            },
            {
                "field": "F_3_4732_F",
                "order": None
            },
            {
                "field": "F_3_4735_F",
                "order": None
            },
            {
                "field": "F_3_4738_F",
                "order": None
            },
            {
                "field": "F_3_4739_F",
                "order": None
            },
            {
                "field": "F_3_4736_F",
                "order": None
            },
            {
                "field": "F_3_4737_F",
                "order": None
            },
            {
                "field": "F_3_4740_F",
                "order": None
            },
            {
                "field": "F_3_4745_F",
                "order": None
            },
            {
                "field": "F_3_4746_F",
                "order": None
            },
            {
                "field": "F_3_4747_F",
                "order": None
            },
            {
                "field": "F_3_26031_F",
                "order": None
            },
            {
                "field": "F_3_4748_F",
                "order": None
            },
            {
                "field": "F_3_4749_F",
                "order": None
            },
            {
                "field": "F_3_4750_F",
                "order": None
            },
            {
                "field": "F_3_4751_F",
                "order": None
            },
            {
                "field": "F_3_4741_F",
                "order": None
            },
            {
                "field": "F_3_7505_F",
                "order": None
            },
            {
                "field": "F_3_7508_F",
                "order": None
            },
            {
                "field": "F_3_4733_F",
                "order": None
            },
            {
                "field": "F_3_4742_F",
                "order": None
            },
            {
                "field": "F_3_4743_F",
                "order": None
            },
            {
                "field": "F_3_4744_F",
                "order": None
            }
        ]
        reportFieldIds = [
            "4714",
            "4715",
            "4716",
            "4721",
            "33528",
            "4732",
            "4735",
            "4738",
            "4739",
            "4736",
            "4737",
            "4740",
            "4745",
            "4746",
            "4747",
            "26031",
            "4748",
            "4749",
            "4750",
            "4751",
            "4741",
            "7505",
            "7508",
            "4733",
            "4742",
            "4743",
            "4744"
        ]
    elif report_code == 31:
        if is_summary:
            orderFields = [
                {
                    "field": "F_3_8129_F",
                    "order": None
                },
                {
                    "field": "F_3_8130_F",
                    "order": None
                },
                {
                    "field": "F_3_8131_F",
                    "order": None
                },
                {
                    "field": "F_3_8137_F",
                    "order": None
                },
                {
                    "field": "F_3_5463_F",
                    "order": None
                },
                {
                    "field": "F_3_7379_F",
                    "order": None
                },
                {
                    "field": "F_3_5464_F",
                    "order": None
                },
                {
                    "field": "F_3_5467_F",
                    "order": None
                },
                {
                    "field": "F_3_5468_F",
                    "order": None
                },
                {
                    "field": "F_3_5469_F",
                    "order": None
                },
                {
                    "field": "F_3_5471_F",
                    "order": None
                },
                {
                    "field": "F_3_5484_F",
                    "order": None
                },
                {
                    "field": "F_3_5474_F",
                    "order": None
                },
                {
                    "field": "F_3_5475_F",
                    "order": None
                },
                {
                    "field": "F_3_5509_F",
                    "order": None
                },
                {
                    "field": "F_3_5510_F",
                    "order": None
                },
                {
                    "field": "F_3_5511_F",
                    "order": None
                },
                {
                    "field": "F_3_5512_F",
                    "order": None
                },
                {
                    "field": "F_3_7443_F",
                    "order": None
                },
                {
                    "field": "F_3_5514_F",
                    "order": None
                },
                {
                    "field": "F_3_7444_F",
                    "order": None
                },
                {
                    "field": "F_3_7462_F",
                    "order": None
                },
                {
                    "field": "F_3_7464_F",
                    "order": None
                }
            ]
            reportFieldIds = [
                "8129",
                "8130",
                "8131",
                "8137",
                "5463",
                "7379",
                "5464",
                "5467",
                "5468",
                "5469",
                "5471",
                "5484",
                "5474",
                "5475",
                "5509",
                "5510",
                "5511",
                "5512",
                "7443",
                "5514",
                "7444",
                "7462",
                "7464"
            ]

        else:
            orderFields = [
                {
                    "field": "F_3_8137_F",
                    "order": None
                },
                {
                    "field": "F_3_5463_F",
                    "order": None
                },
                {
                    "field": "F_3_7379_F",
                    "order": None
                },
                {
                    "field": "F_3_5464_F",
                    "order": None
                },
                {
                    "field": "F_3_5467_F",
                    "order": None
                },
                {
                    "field": "F_3_5468_F",
                    "order": None
                },
                {
                    "field": "F_3_5469_F",
                    "order": None
                },
                {
                    "field": "F_3_5471_F",
                    "order": None
                },
                {
                    "field": "F_3_5484_F",
                    "order": None
                },
                {
                    "field": "F_3_5474_F",
                    "order": None
                },
                {
                    "field": "F_3_5475_F",
                    "order": None
                },
                {
                    "field": "F_3_5509_F",
                    "order": None
                },
                {
                    "field": "F_3_5510_F",
                    "order": None
                },
                {
                    "field": "F_3_5511_F",
                    "order": None
                },
                {
                    "field": "F_3_5512_F",
                    "order": None
                },
                {
                    "field": "F_3_7443_F",
                    "order": None
                },
                {
                    "field": "F_3_5514_F",
                    "order": None
                },
                {
                    "field": "F_3_7444_F",
                    "order": None
                },
                {
                    "field": "F_3_7462_F",
                    "order": None
                },
                {
                    "field": "F_3_7464_F",
                    "order": None
                }
            ]
            reportFieldIds = [
                "8137",
                "5463",
                "7379",
                "5464",
                "5467",
                "5468",
                "5469",
                "5471",
                "5484",
                "5474",
                "5475",
                "5509",
                "5510",
                "5511",
                "5512",
                "7443",
                "5514",
                "7444",
                "7462",
                "7464"
            ]

    elif report_code == 185:
        if is_summary:
            orderFields = [
                {
                    "field": "F_3_27338_F",
                    "order": None
                },
                {
                    "field": "F_3_27334_F",
                    "order": None
                },
                {
                    "field": "F_3_27326_F",
                    "order": None
                },
                {
                    "field": "F_3_27327_F",
                    "order": None
                },
                {
                    "field": "F_3_27328_F",
                    "order": None
                },
                {
                    "field": "F_3_34821_F",
                    "order": None
                },
                {
                    "field": "F_3_27388_F",
                    "order": None
                },
                {
                    "field": "F_3_103755_F",
                    "order": None
                },
                {
                    "field": "F_3_103756_F",
                    "order": None
                },
                {
                    "field": "F_3_27389_F",
                    "order": None
                },
                {
                    "field": "F_3_27390_F",
                    "order": None
                },
                {
                    "field": "F_3_128514_F",
                    "order": None
                },
                {
                    "field": "F_3_128513_F",
                    "order": None
                },
                {
                    "field": "F_3_34823_F",
                    "order": None
                },
                {
                    "field": "F_3_120733_F",
                    "order": None
                }
            ]
            reportFieldIds = [
                "27338",
                "27334",
                "27326",
                "27327",
                "27328",
                "34821",
                "27388",
                "103755",
                "103756",
                "27389",
                "27390",
                "128514",
                "128513",
                "34823",
                "120733"
            ]
        else:
            orderFields = [
                {
                    "field": "F_3_27338_F",
                    "order": None
                },
                {
                    "field": "F_3_27348_F",
                    "order": None
                },
                {
                    "field": "F_3_27349_F",
                    "order": None
                },
                {
                    "field": "F_3_27350_F",
                    "order": None
                },
                {
                    "field": "F_3_27351_F",
                    "order": None
                },
                {
                    "field": "F_3_27357_F",
                    "order": None
                },
                {
                    "field": "F_3_27352_F",
                    "order": None
                },
                {
                    "field": "F_3_27359_F",
                    "order": None
                },
                {
                    "field": "F_3_27353_F",
                    "order": None
                },
                {
                    "field": "F_3_27363_F",
                    "order": "ascend"
                },
                {
                    "field": "F_3_27388_F",
                    "order": None
                },
                {
                    "field": "F_3_103755_F",
                    "order": None
                },
                {
                    "field": "F_3_103756_F",
                    "order": None
                },
                {
                    "field": "F_3_27389_F",
                    "order": None
                },
                {
                    "field": "F_3_27390_F",
                    "order": None
                },
                {
                    "field": "F_3_34823_F",
                    "order": None
                },
                {
                    "field": "F_3_120733_F",
                    "order": None
                }
            ]
            reportFieldIds = [
                "27338",
                "27348",
                "27349",
                "27350",
                "27351",
                "27357",
                "27352",
                "27359",
                "27353",
                "27363",
                "27388",
                "103755",
                "103756",
                "27389",
                "27390",
                "34823",
                "120733"
            ]
    else:
        orderFields = None
        reportFieldIds = None
    data_json = {"orderFields": orderFields, "reportFieldIds": reportFieldIds}
    return data_json
