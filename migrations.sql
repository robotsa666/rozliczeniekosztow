
-- DDL
create table if not exists public.opk_nodes (
  node_id text primary key,
  parent_id text references public.opk_nodes(node_id) on delete set null,
  level int not null,
  name text not null,
  path_labels text[] not null,
  path_text text generated always as (array_to_string(path_labels, ' > ')) stored,
  owner_id uuid not null references auth.users(id),
  created_at timestamptz default now(),
  updated_at timestamptz default now()
);

create table if not exists public.allocation_rules (
  rule_id bigint generated always as identity primary key,
  parent_id text not null references public.opk_nodes(node_id) on delete cascade,
  child_id text not null references public.opk_nodes(node_id) on delete cascade,
  method text not null check (method in ('KVI','EQUAL','MANUAL')),
  weight numeric,
  amount numeric,
  valid_from date,
  valid_to date,
  owner_id uuid not null references auth.users(id),
  created_at timestamptz default now()
);

create table if not exists public.cost_transactions (
  tx_id bigint generated always as identity primary key,
  doc_no text,
  doc_date date not null,
  period text not null,
  opk_id text not null references public.opk_nodes(node_id) on delete set null,
  amount numeric not null,
  description text,
  owner_id uuid not null references auth.users(id),
  created_at timestamptz default now()
);

create table if not exists public.allocations (
  alloc_id bigint generated always as identity primary key,
  period text not null,
  source_opk text not null references public.opk_nodes(node_id) on delete cascade,
  target_opk text not null references public.opk_nodes(node_id) on delete cascade,
  method text not null,
  base_amount numeric not null,
  share numeric not null,
  amount numeric not null,
  rule_id bigint references public.allocation_rules(rule_id),
  owner_id uuid not null references auth.users(id),
  created_at timestamptz default now()
);

-- Indexes
create index if not exists idx_opk_nodes_parent on public.opk_nodes(parent_id);
create index if not exists idx_rules_parent on public.allocation_rules(parent_id);
create index if not exists idx_costs_period_opk on public.cost_transactions(period, opk_id);
create index if not exists idx_alloc_period_src_tgt on public.allocations(period, source_opk, target_opk);

-- RLS
alter table public.opk_nodes enable row level security;
alter table public.allocation_rules enable row level security;
alter table public.cost_transactions enable row level security;
alter table public.allocations enable row level security;

create policy opk_nodes_sel on public.opk_nodes for select using (owner_id = auth.uid());
create policy opk_nodes_ins on public.opk_nodes for insert with check (owner_id = auth.uid());
create policy opk_nodes_upd on public.opk_nodes for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy opk_nodes_del on public.opk_nodes for delete using (owner_id = auth.uid());

create policy rules_sel on public.allocation_rules for select using (owner_id = auth.uid());
create policy rules_ins on public.allocation_rules for insert with check (owner_id = auth.uid());
create policy rules_del on public.allocation_rules for delete using (owner_id = auth.uid());
create policy rules_upd on public.allocation_rules for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());

create policy costs_sel on public.cost_transactions for select using (owner_id = auth.uid());
create policy costs_ins on public.cost_transactions for insert with check (owner_id = auth.uid());
create policy costs_upd on public.cost_transactions for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy costs_del on public.cost_transactions for delete using (owner_id = auth.uid());

create policy alloc_sel on public.allocations for select using (owner_id = auth.uid());
create policy alloc_ins on public.allocations for insert with check (owner_id = auth.uid());
create policy alloc_upd on public.allocations for update using (owner_id = auth.uid()) with check (owner_id = auth.uid());
create policy alloc_del on public.allocations for delete using (owner_id = auth.uid());
