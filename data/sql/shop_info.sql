select sto_c.tenant_id,
  tt.name as 'tenant_name',
  sto_c.enterprise_id,
  ent.name as 'enterprise_name',
  ent.credit_code as 'enterprise_credit_code',
  sto_c.store_id,
  sto_c.store_code,
  sto.name as 'store_name',
  sto.credit_code as 'store_credit_code',
  sto_c.shop_code,
  sto_c.shop_name as 'shop_name'
from rl_shop_config sto_c
  left join salus_base.bs_stores sto on sto.tenant_id = sto_c.tenant_id
  and sto.enterprise_id = sto_c.enterprise_id
  and sto.id = sto_c.store_id
  left join salus_base.bs_enterprise ent on ent.tenant_id = sto_c.tenant_id
  and ent.id = sto_c.enterprise_id
  left join salus_base.sys_tenant tt on tt.id = sto_c.tenant_id
  left join salus_base.cm_license cl on cl.tenant_id = sto_c.tenant_id
  and cl.enterprise_id = sto_c.enterprise_id
where sto_c.shop_status = {shop_status} # 店铺状态, 0: 禁用 1: 启用
  and sto_c.tenant_id = 2234 # 租户ID
  and sto_c.deleted = 0
  and cl.status = 1 # 店铺是否有效
  {search_name_where} # 搜索名称
;
