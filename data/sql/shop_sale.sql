select sale.tenant_id,
    sale.enterprise_id,
    ent.name as 'enterprise_name',
    sale.shop_code,
    sale.shop_name,
    count(sale.order_id) as 'number_of_orders',
    sum(sale.total_amount) as 'amount_receivable',
    sum(sale.pay_amount) as 'amount_received',
    round(sum(sale_cost.cost), 2) as 'cost_amount',
    round(sum(sale.pay_amount) - sum(sale_cost.cost), 2) as 'gross_profit',
    sum(sale.discount_amount) as 'discount_amount',
    round(sum(sale.pay_amount) / count(sale.order_id), 2) as 'average_order_value',
    round(
        (sum(sale.pay_amount) - sum(sale_cost.cost)) / sum(sale.pay_amount),
        4
    ) as 'gross_profit_margin'
from o_order sale
    left join (
        select tenant_id,
            enterprise_id,
            order_id,
            sum(max_cost_price * quantity) as cost
        from o_order_item
        group by tenant_id,
            enterprise_id,
            order_id
    ) sale_cost on sale_cost.tenant_id = sale.tenant_id
    and sale_cost.enterprise_id = sale.enterprise_id
    and sale_cost.order_id = sale.order_id
    left join salus_base.bs_enterprise ent on ent.tenant_id = sale.tenant_id
    and ent.id = sale.enterprise_id
    left join rl_shop_config sto_c on sto_c.tenant_id = sale.tenant_id
    and sto_c.enterprise_id = sale.enterprise_id
    and sto_c.shop_code = sale.shop_code
where sale.tenant_id = 2234
    and sale.deleted = 0
    and sale.status = 10
    and sale.order_sub_type = 1
    and sale.pay_status = 3
    and sale.buyer_order_pay_time between '{star_date}' and '{end_date}' 
    {shop_name_where} 
    {shop_code_where}
    {store_code_where}
group by sale.tenant_id,
    sale.enterprise_id,
    sale.shop_code,
    sale.shop_name;