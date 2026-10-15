"""
商品模块
"""

from httpx import AsyncClient
from typing import Optional, List

from configs.api_config import deming_env
from api.virtue_bright.general_tools import timestamp, get_current_date, get_date_start_and_end_time
from utils.logger_manager import LoggerManager

logger = LoggerManager.get_logger(name=__name__)

yaoud_env = deming_env
base_url = f"{yaoud_env['url']}/product/bs"
TTL = yaoud_env["timeout"]


async def goods_page_list(
        authorization: str,
        tenant_id: Optional[int] = None,
        current: int = 1,
        size: int = 20,
        sortCode: Optional[str] = None,
        orders: Optional[str] = None,

        keywordNew: Optional[str] = None,

        codes: Optional[str] = None,
        yaoudCodes: Optional[str] = None,
        commonName: Optional[str] = None,
        commonAbc: Optional[str] = None,
        name: Optional[str] = None,
        abc: Optional[str] = None,
        barcode: Optional[str] = None,
        barcodeSecond: Optional[str] = None,
        maxBarcode: Optional[str] = None,
        midBarcode: Optional[str] = None,
        splitBarcode: Optional[str] = None,
        breedCode: Optional[str] = None,
        provinceBreedCode: Optional[str] = None,
        insuLevels: Optional[List[str]] = None,
        drugStandardCode: Optional[str] = None,
        spec: Optional[str] = None,
        preparationSpec: Optional[str] = None,
        remark: Optional[str] = None,
        archivesCode: Optional[str] = None,
        pricePrintingTag: Optional[str] = None,
        buyTaxs: Optional[List[str]] = None,
        saleTaxs: Optional[List[str]] = None,
        imagelDetails: Optional[str] = None,
        insChemistryName: Optional[str] = None,
        insMainComponents: Optional[str] = None,
        insCharacter: Optional[str] = None,
        insAction: Optional[str] = None,
        insFunction: Optional[str] = None,
        insUsageDosage: Optional[str] = None,
        insTaboo: Optional[str] = None,
        insAdverseReactions: Optional[str] = None,
        insNote: Optional[str] = None,
        insDrugInteractions: Optional[str] = None,
        insDrugOverdose: Optional[str] = None,
        insStorage: Optional[str] = None,
        insPackage: Optional[str] = None,
        insExecutiveStandards: Optional[str] = None,
        customOne: Optional[str] = None,
        customTwo: Optional[str] = None,
        customThree: Optional[str] = None,
        customSixList: Optional[List[str]] = None,

        producer: Optional[str] = None,
        entrustedProducer: Optional[str] = None,
        proAddress: Optional[str] = None,
        licenseNumber: Optional[str] = None,
        listingPermitHolder: Optional[str] = None,
        registeredPerson: Optional[str] = None,
        filingPerson: Optional[str] = None,
        filingPersonAddress: Optional[str] = None,

        licenseType: Optional[str] = None,
        permitCode: Optional[str] = None,

        validityAlertDaysStart: Optional[str] = None,
        validityAlertDaysEnd: Optional[str] = None,
        createStartDate: Optional[str] = None,
        createEndDate: Optional[str] = None,
        updateStartDate: Optional[str] = None,
        updateEndDate: Optional[str] = None,

        minDaysForNearWarn: Optional[int] = None,
        maxDaysForNearWarn: Optional[int] = None,
        minInStorageValidityDays: Optional[int] = None,
        maxInStorageValidityDays: Optional[int] = None,
        minOutStorageValidityDays: Optional[int] = None,
        maxOutStorageValidityDays: Optional[int] = None,
        minRetailValidityDays: Optional[int] = None,
        maxRetailValidityDays: Optional[int] = None,
        minInsPayPrice: Optional[int] = None,
        maxInsPayPrice: Optional[int] = None,
        minInsAdjustRate: Optional[int] = None,
        maxInsAdjustRate: Optional[int] = None,
        minInsPayStandard: Optional[int] = None,
        maxInsPayStandard: Optional[int] = None,
        minMaxQty: Optional[int] = None,
        maxMaxQty: Optional[int] = None,
        minMidQty: Optional[int] = None,
        maxMidQty: Optional[int] = None,
        minDose: Optional[int] = None,
        maxDose: Optional[int] = None,
        minAdjustMinPrice: Optional[int] = None,
        maxAdjustMinPrice: Optional[int] = None,
        minAdjustMinDiscount: Optional[int] = None,
        maxAdjustMinDiscount: Optional[int] = None,
        minLimitPrice: Optional[int] = None,
        maxLimitPrice: Optional[int] = None,
        minSplitPrice: Optional[int] = None,
        maxSplitPrice: Optional[int] = None,
        minSplitMemberPrice: Optional[int] = None,
        maxSplitMemberPrice: Optional[int] = None,
        minSplitValue: Optional[int] = None,
        maxSplitValue: Optional[int] = None,
        minRetailPrice: Optional[int] = None,
        maxRetailPrice: Optional[int] = None,
        minMembershipPrice: Optional[int] = None,
        maxMembershipPrice: Optional[int] = None,
        minUseDays: Optional[int] = None,
        maxUseDays: Optional[int] = None,
        minUseBoxes: Optional[int] = None,
        maxUseBoxes: Optional[int] = None,
        minInsValidity: Optional[int] = None,
        maxInsValidity: Optional[int] = None,

        insValidityTypes: Optional[List[str]] = None,
        isEnables: Optional[List[int]] = None,
        isGspinfos: Optional[List[int]] = None,
        isNewss: Optional[List[int]] = None,
        isImports: Optional[List[int]] = None,
        isMidDeliveryRequests: Optional[List[int]] = None,
        isNullBreedCode: Optional[int] = 0,
        isBuckets: Optional[List[int]] = None,
        isTwoChecks: Optional[List[int]] = None,
        isInspectionReports: Optional[List[int]] = None,
        isAllocates: Optional[List[int]] = None,
        isAllowBuys: Optional[List[int]] = None,
        isInsus: Optional[List[int]] = None,
        isOverallPlans: Optional[List[int]] = None,
        isPriceLimits: Optional[List[int]] = None,
        isDoubleCrosss: Optional[List[int]] = None,
        conserveTypes: Optional[List[str]] = None,
        isEnableTraceCodes: Optional[List[int]] = None,
        isMinTraceCodes: Optional[List[int]] = None,
        traceCodeTypes: Optional[List[str]] = None,
        prescriptionControlMarks: Optional[List[str]] = None,
        isSplits: Optional[List[int]] = None,
        isPriceMaintainedList: Optional[List[int]] = None,
        isSpecialPriceList: Optional[List[int]] = None,

        classTypes: Optional[List[str]] = None,
        businessRanges: Optional[List[str]] = None,
        labelIds: Optional[List[str]] = None,
        purchaseIds: Optional[List[str]] = None,
        createIds: Optional[List[str]] = None,
        updateIds: Optional[List[str]] = None,
        productTypes: Optional[List[str]] = None,

        productionRanges: Optional[List[str]] = None,
        dosages: Optional[List[str]] = None,
        specialTypes: Optional[List[str]] = None,
        prescriptionTypes: Optional[List[str]] = None,
        storageTypes: Optional[List[str]] = None,
        baseUnits: Optional[List[str]] = None,
        maxUnits: Optional[List[str]] = None,
        midUnits: Optional[List[str]] = None,
        doseUnits: Optional[List[str]] = None,
        taxClassificationCodes: Optional[List[str]] = None,
        splitUnits: Optional[List[str]] = None,
        productSecondTypes: Optional[List[str]] = None,) -> dict:
    """
    商品资料查询(企业级)
    Args:
        authorization (str): 授权token，格式为"Bearer <token>"
        tenant_id (int, None): 租户ID. Defaults to None.
        current (int): 当前页. Defaults to 1.
        size (int): 每页数据数量. Defaults to 20.
        sortCode(str, None): 排序字段. Defaults to None.
        orders(str, None): 排序方式. Defaults to None.

        keywordNew(str, None): 关键词. Defaults to None.
            - 商品编码，助记码，商品名称，通用名称，商品条码
        codes(str, None): 商品编码. Defaults to None.
        yaoudCodes(str, None): 药德编码. Defaults to None.
        commonName(str, None): 通用名称. Defaults to None.
        commonAbc(str, None): 通用名称助记码. Defaults to None.
        name(str, None): 商品名称. Defaults to None.
        abc(str, None): 商品名称助记码. Defaults to None.
        barcode(str, None): 商品条码. Defaults to None.
        barcodeSecond(str, None): 商品条码2. Defaults to None.
        maxBarcode(str, None): 件包装条码. Defaults to None.
        midBarcode(str, None): 中包装条码. Defaults to None.
        splitBarcode(str, None): 拆零条码. Defaults to None.
        breedCode(str, None): 国家医保编码. Defaults to None.
        provinceBreedCode(str, None): 地方医保编码. Defaults to None.
        insuLevels(List[str], None): 医保等级. Defaults to None.
        drugStandardCode(str, None): 药品本位码. Defaults to None.
        spec(str, None): 规格. Defaults to None.
        preparationSpec(str, None): 制剂规格. Defaults to None.
        remark(str, None): 备注. Defaults to None.
        archivesCode(str, None): 档案号. Defaults to None.
        pricePrintingTag(str, None): 价格标签标识. Defaults to None.
        buyTaxs(List[str], None): 进项税率("0.01"). Defaults to None.
        saleTaxs(List[str], None): 销项税率("0.01"). Defaults to None.
        imagelDetails(str, None): 图文说明. Defaults to None.
        insChemistryName(str, None): 化学名称. Defaults to None.
        insMainComponents(str, None): 主要成分. Defaults to None.
        insCharacter(str, None): 性状. Defaults to None.
        insAction(str, None): 作用类别. Defaults to None.
        insFunction(str, None): 功能主治. Defaults to None.
        insUsageDosage(str, None): 用法用量. Defaults to None.
        insTaboo(str, None): 禁忌. Defaults to None.
        insAdverseReactions(str, None): 不良反应. Defaults to None.
        insNote(str, None): 注意事项. Defaults to None.
        insDrugInteractions(str, None): 药物相互作用. Defaults to None.
        insDrugOverdose(str, None): 药物过量. Defaults to None.
        insStorage(str, None): 贮藏. Defaults to None.
        insPackage(str, None): 包装. Defaults to None.
        insExecutiveStandards(str, None): 执行标准. Defaults to None.
        customOne(str, None): 自定义字段1. Defaults to None.
        customTwo(str, None): 自定义字段2. Defaults to None.
        customThree(str, None): 自定义字段3. Defaults to None.
        customSixList(List[str], None): 自定义字段6列表. Defaults to None.
        producer(str, None): 生产企业. Defaults to None.
        entrustedProducer(str, None): 委托生产企业. Defaults to None.
        proAddress(str, None): 产地. Defaults to None.
        licenseNumber(str, None): 批准文号/注册证号/备案号. Defaults to None.
        listingPermitHolder(str, None): 上市许可持有人. Defaults to None.
        registeredPerson(str, None): 注册人. Defaults to None.
        filingPerson(str, None): 备案人. Defaults to None.
        filingPersonAddress(str, None): 备案人地址. Defaults to None.
        licenseType(str, None): 许可类型. Defaults to None.
        permitCode(str, None): 许可编号. Defaults to None.
        validityAlertDaysStart(str, None): 有效期预警区间-开始. Defaults to None.
            - 日期格式为yyyy-MM-dd
        validityAlertDaysEnd(str, None): 有效期预警区间-结束. Defaults to None.
            - 日期格式为yyyy-MM-dd
        createStartDate(str, None): 创建时间区间-开始. Defaults to None.
            - 日期格式为yyyy-MM-dd
        createEndDate(str, None): 创建时间区间-结束. Defaults to None.
            - 日期格式为yyyy-MM-dd
        updateStartDate(str, None): 更新时间区间-开始. Defaults to None.
            - 日期格式为yyyy-MM-dd
        updateEndDate(str, None): 更新时间区间-结束. Defaults to None.
            - 日期格式为yyyy-MM-dd
        minDaysForNearWarn(int, None): 近效期预警天数-最小值
        maxDaysForNearWarn(int, None): 近效期预警天数-最大值
        minInStorageValidityDays(int, None): 在库有效期天数-最小值
        maxInStorageValidityDays(int, None): 在库有效期天数-最大值
        minOutStorageValidityDays(int, None): 出库有效期天数-最小值
        maxOutStorageValidityDays(int, None): 出库有效期天数-最大值
        minRetailValidityDays(int, None): 零售有效期天数-最小值
        maxRetailValidityDays(int, None): 零售有效期天数-最大值
        minInsPayPrice(int, None): 医保支付价格-最小值
        maxInsPayPrice(int, None): 医保支付价格-最大值
        minInsAdjustRate(int, None): 医保调整率-最小值
        maxInsAdjustRate(int, None): 医保调整率-最大值
        minInsPayStandard(int, None): 医保支付标准-最小值
        maxInsPayStandard(int, None): 医保支付标准-最大值
        minMaxQty(int, None): 最大库存量-最小值
        maxMaxQty(int, None): 最大库存量-最大值
        minMidQty(int, None): 中包装库存量-最小值
        maxMidQty(int, None): 中包装库存量-最大值
        minDose(int, None): 剂量-最小值
        maxDose(int, None): 剂量-最大值
        minAdjustMinPrice(int, None): 最低调整价格-最小值
        maxAdjustMinPrice(int, None): 最低调整价格-最大值
        minAdjustMinDiscount(int, None): 最低调整折扣-最小值
        maxAdjustMinDiscount(int, None): 最低调整折扣-最大值
        minLimitPrice(int, None): 最低限价-最小值
        maxLimitPrice(int, None): 最低限价-最大值
        minSplitPrice(int, None): 拆零价格-最小值
        maxSplitPrice(int, None): 拆零价格-最大值   
        minSplitMemberPrice(int, None): 拆零会员价格-最小值
        maxSplitMemberPrice(int, None): 拆零会员价格-最大值
        minSplitValue(int, None): 拆零数量-最小值
        maxSplitValue(int, None): 拆零数量-最大值
        minRetailPrice(int, None): 零售价格-最小值
        maxRetailPrice(int, None): 零售价格-最大值
        minMembershipPrice(int, None): 会员价格-最小值  
        maxMembershipPrice(int, None): 会员价格-最大值
        minUseDays(int, None): 使用天数-最小值
        maxUseDays(int, None): 使用天数-最大值
        minUseBoxes(int, None): 使用盒数-最小值
        maxUseBoxes(int, None): 使用盒数-最大值
        minInsValidity(int, None): 医保有效期-最小值
        maxInsValidity(int, None): 医保有效期-最大值
        insValidityTypes(List[str], None): 有效期类型. Defaults to None.
        isEnables(List[int], None): 是否启用. Defaults to None.
            - 1-是
            - 0-否
        isGspinfos(List[int], None): 是否已首营.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        isNewss(List[int], None): 是否新品. Defaults to None.
            - 1-是
            - 0-否
        isImports(List[int], None): 是否进口. Defaults to None.
            - 1-是
            - 0-否
        isMidDeliveryRequests(List[int], None): 是否中包装请货. Defaults to None.
            - 1-是
            - 0-否
        isNullBreedCode(int, None): 是否国家医保编码为空. Defaults to 0.
            - 1-是
            - 0-否
        isBuckets(List[int], None): 是否装斗.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        isTwoChecks(List[int], None): 是否双检或复检. Defaults to None.
            - 1-是
            - 0-否
        isInspectionReports(List[int], None): 是否需提供检验报告.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        isAllocates(List[int], None): 是否允许调拨. Defaults to None.
            - 1-是
            - 0-否
        isAllowBuys(List[int], None): 是否允许采购. Defaults to None.
            - 1-是
            - 0-否
        isInsus(List[int], None): 是否医保商品.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        isOverallPlans(List[int], None): 是否统筹商品. Defaults to None.
            - 1-是
            - 0-否
        isPriceLimits(List[int], None): 是否限价.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        isDoubleCrosss(List[int], None): 是否双跨.1-是，0-否 Defaults to None.
            - 1-是
            - 0-否
        conserveTypes(List[str], None): 养护类型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=养护类型
        isEnableTraceCodes(List[int], None): 是否启用追溯码. Defaults to None.
            - 1-是
            - 0-否
        isMinTraceCodes(List[int], None): 是否最小追溯码. Defaults to None.
            - 1-是
            - 0-否
        traceCodeTypes(List[str], None): 追溯码类型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=追溯码类型
        prescriptionControlMarks(List[str], None): 处方管控类型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=处方管控类型
            - 0-不管控
            - 1-非长处方
            - 2-长处方
        isSplits(List[int], None): 是否拆零. Defaults to None.
            - 1-是  
            - 0-否
        isPriceMaintainedList(List[int], None): 是否维价商品. Defaults to None.
            - 1-是
            - 0-否
        isSpecialPriceList(List[int], None): 是否特价商品. Defaults to None.
            - 1-是
            - 0-否
        classTypes(List[str], None): 商品分类. Defaults to None.
            - 可在 user_product_class_tree 中获取
        businessRanges(List[str], None): 经营范围.Defaults to None.
            - 可在 business_scope_tree_list 中获取
        labelIds(List[str], None): 标签ID. Defaults to None.
            - 可在 goods_label_type_tree 中获取
        purchaseIds(List[str], None): 采购ID. Defaults to None.
            - 可在 employee_page 中获取 postCodeList 为 POST_BUYER
        createIds(List[str], None): 创建人ID. Defaults to None.
            - 可在 employee_page 中获取
        updateIds(List[str], None): 更新人ID. Defaults to None.
            - 可在 employee_page 中获取
        productTypes(List[str], None): 商品类型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=商品类型
        productionRanges(List[str], None): 生产范围. Defaults to None.
            - 可在 production_scope_tree 中获取
        dosages(List[str], None): 剂型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=剂型
        specialTypes(List[str], None): 特殊药品. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=特殊药品类型
        prescriptionTypes(List[str], None): 处方药. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=处方类型
        storageTypes(List[str], None): 储存条件. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=贮存条件
        baseUnits(List[str], None): 基本单位. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=基本单位
        maxUnits(List[str], None): 件包装单位. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=件包装单位
        midUnits(List[str], None): 中包装单位. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=中包装单位
        doseUnits(List[str], None): 剂量单位. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=剂量单位
        taxClassificationCodes(List[str], None): 商品税分类编码. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=商品税收分类
        splitUnits(List[str], None): 拆零单位. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=拆零单位
        productSecondTypes(List[str], None): 商品二级类型. Defaults to None.
            - 可在 dict_item_list 中获取, keyword=商品二级类型
    Returns:
        dict: 商品资料查询结果
    """
    url = f"{base_url}/goods/pageList"
    headers = {
        "authorization": authorization,  # 必须
        "client-tom": "Y",
        "tenant-id": str(tenant_id) if tenant_id else "",
    }

    payload = {
        "current": current,
        "size": size,
        "keywordNew": keywordNew,
        "sortCode": sortCode,
        "orders": orders,
        "codes": codes,
        "yaoudCodes": yaoudCodes,
        "commonName": commonName,
        "commonAbc": commonAbc,
        "name": name,
        "abc": abc,
        "barcode": barcode,
        "barcodeSecond": barcodeSecond,
        "maxBarcode": maxBarcode,
        "midBarcode": midBarcode,
        "splitBarcode": splitBarcode,
        "breedCode": breedCode,
        "provinceBreedCode": provinceBreedCode,
        "insuLevels": insuLevels,
        "drugStandardCode": drugStandardCode,
        "spec": spec,
        "preparationSpec": preparationSpec,
        "remark": remark,
        "archivesCode": archivesCode,
        "pricePrintingTag": pricePrintingTag,
        "buyTaxs": buyTaxs,
        "saleTaxs": saleTaxs,
        "imagelDetails": imagelDetails,
        "insChemistryName": insChemistryName,
        "insMainComponents": insMainComponents,
        "insCharacter": insCharacter,
        "insAction": insAction,
        "insFunction": insFunction,
        "insUsageDosage": insUsageDosage,
        "insTaboo": insTaboo,
        "insAdverseReactions": insAdverseReactions,
        "insNote": insNote,
        "insDrugInteractions": insDrugInteractions,
        "insDrugOverdose": insDrugOverdose,
        "insStorage": insStorage,
        "insPackage": insPackage,
        "insExecutiveStandards": insExecutiveStandards,
        "customOne": customOne,
        "customTwo": customTwo,
        "customThree": customThree,
        "customSixList": customSixList,
        "producer": producer,
        "entrustedProducer": entrustedProducer,
        "proAddress": proAddress,
        "licenseNumber": licenseNumber,
        "listingPermitHolder": listingPermitHolder,
        "registeredPerson": registeredPerson,
        "filingPerson": filingPerson,
        "filingPersonAddress": filingPersonAddress,
        "licenseType": licenseType,
        "permitCode": permitCode,

        "validityAlertDaysStart": validityAlertDaysStart,
        "validityAlertDaysEnd": validityAlertDaysEnd,
        "createStartDate": createStartDate,
        "createEndDate": createEndDate,
        "updateStartDate": updateStartDate,
        "updateEndDate": updateEndDate,

        "minDaysForNearWarn": minDaysForNearWarn,
        "maxDaysForNearWarn": maxDaysForNearWarn,
        "minInStorageValidityDays": minInStorageValidityDays,
        "maxInStorageValidityDays": maxInStorageValidityDays,
        "minOutStorageValidityDays": minOutStorageValidityDays,
        "maxOutStorageValidityDays": maxOutStorageValidityDays,
        "minRetailValidityDays": minRetailValidityDays,
        "maxRetailValidityDays": maxRetailValidityDays,
        "minInsPayPrice": minInsPayPrice,
        "maxInsPayPrice": maxInsPayPrice,
        "minInsAdjustRate": minInsAdjustRate,
        "maxInsAdjustRate": maxInsAdjustRate,
        "minInsPayStandard": minInsPayStandard,
        "maxInsPayStandard": maxInsPayStandard,
        "minMaxQty": minMaxQty,
        "maxMaxQty": maxMaxQty,
        "minMidQty": minMidQty,
        "maxMidQty": maxMidQty,
        "minDose": minDose,
        "maxDose": maxDose,
        "minAdjustMinPrice": minAdjustMinPrice,
        "maxAdjustMinPrice": maxAdjustMinPrice,
        "minAdjustMinDiscount": minAdjustMinDiscount,
        "maxAdjustMinDiscount": maxAdjustMinDiscount,
        "minLimitPrice": minLimitPrice,
        "maxLimitPrice": maxLimitPrice,
        "minSplitPrice": minSplitPrice,
        "maxSplitPrice": maxSplitPrice,
        "minSplitMemberPrice": minSplitMemberPrice,
        "maxSplitMemberPrice": maxSplitMemberPrice,
        "minSplitValue": minSplitValue,
        "maxSplitValue": maxSplitValue,
        "minRetailPrice": minRetailPrice,
        "maxRetailPrice": maxRetailPrice,
        "minMembershipPrice": minMembershipPrice,
        "maxMembershipPrice": maxMembershipPrice,
        "minUseDays": minUseDays,
        "maxUseDays": maxUseDays,
        "minUseBoxes": minUseBoxes,
        "maxUseBoxes": maxUseBoxes,
        "minInsValidity": minInsValidity,
        "maxInsValidity": maxInsValidity,

        "insValidityTypes": insValidityTypes,
        "isEnables": isEnables,
        "isGspinfos": isGspinfos,
        "isNewss": isNewss,
        "isImports": isImports,
        "isMidDeliveryRequests": isMidDeliveryRequests,
        "isNullBreedCode": isNullBreedCode,
        "isBuckets": isBuckets,
        "isTwoChecks": isTwoChecks,
        "isInspectionReports": isInspectionReports,
        "isAllocates": isAllocates,
        "isAllowBuys": isAllowBuys,
        "isInsus": isInsus,
        "isOverallPlans": isOverallPlans,
        "isPriceLimits": isPriceLimits,
        "isDoubleCrosss": isDoubleCrosss,
        "conserveTypes": conserveTypes,
        "isEnableTraceCodes": isEnableTraceCodes,
        "isMinTraceCodes": isMinTraceCodes,
        "traceCodeTypes": traceCodeTypes,
        "prescriptionControlMarks": prescriptionControlMarks,
        "isSplits": isSplits,
        "isPriceMaintainedList": isPriceMaintainedList,
        "isSpecialPriceList": isSpecialPriceList,

        "classTypes": classTypes,
        "businessRanges": businessRanges,
        "productTypes": productTypes,
        "labelIds": labelIds,
        "purchaseIds": purchaseIds,
        "createIds": createIds,
        "updateIds": updateIds,

        "productionRanges": productionRanges,
        "dosages": dosages,
        "specialTypes": specialTypes,
        "prescriptionTypes": prescriptionTypes,
        "storageTypes": storageTypes,
        "baseUnits": baseUnits,
        "maxUnits": maxUnits,
        "midUnits": midUnits,
        "doseUnits": doseUnits,
        "taxClassificationCodes": taxClassificationCodes,
        "splitUnits": splitUnits,
        "productSecondTypes": productSecondTypes,
    }
    async with AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload, timeout=TTL)
    return response.json()


if __name__ == "__main__":
    import asyncio

    authorization = "Bearer new_05c51760-b65b-46eb-9d2a-f938aa261ee7"
    data = asyncio.run(goods_page_list(authorization=authorization, keywordNew="枸橼酸西地那非片"))
    print(data)