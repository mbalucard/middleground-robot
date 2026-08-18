select distinct sale.tenant_id,
    sale.enterprise_id,
    ent.name as enterprise_name,
    stores.store_code,
    stores.name as store_name,
    sale.shop_code,
    sale.shop_name
from o_order sale
    left join salus_base.bs_enterprise ent on ent.tenant_id = sale.tenant_id
    and ent.id = sale.enterprise_id
    left join (
        select sto_c.tenant_id,
            sto_c.enterprise_id,
            sto_c.store_code,
            sto.name,
            sto_c.shop_code,
            sto_c.shop_name
        from rl_shop_config sto_c
            left join salus_base.bs_stores sto on sto.tenant_id = sto_c.tenant_id
            and sto.enterprise_id = sto_c.enterprise_id
            and sto.id = sto_c.store_id
    ) stores on stores.tenant_id = sale.tenant_id
    and stores.enterprise_id = sale.enterprise_id
    and stores.shop_code = sale.shop_code
where sale.tenant_id = 2234
    and sale.buyer_order_pay_time between '{star_date}' and '{end_date}'
    {search_name_where}
    ;