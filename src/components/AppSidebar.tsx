import {
  LayoutDashboard, FileText, History, Users, Wrench, BarChart3, Zap, LogOut, Settings, CircuitBoard
} from "lucide-react";
import { NavLink } from "@/components/NavLink";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  Sidebar, SidebarContent, SidebarGroup, SidebarGroupContent, SidebarGroupLabel,
  SidebarMenu, SidebarMenuButton, SidebarMenuItem, SidebarFooter, useSidebar,
} from "@/components/ui/sidebar";

const mainItems = [
  { title: "Dashboard", url: "/dashboard", icon: LayoutDashboard },
  { title: "Ocorrências", url: "/ocorrencias", icon: FileText },
  { title: "Histórico", url: "/historico", icon: History },
];

const managementItems = [
  { title: "Colaboradores", url: "/colaboradores", icon: Users },
  { title: "Equipamentos", url: "/equipamentos", icon: Settings },
];

const servicesItems = [
  { title: "Motores Elétricos", url: "/motores-eletricos", icon: CircuitBoard },
];

const reportsItems = [
  { title: "Resumo Mensal", url: "/resumo-mensal", icon: BarChart3 },
  { title: "Automações", url: "/automacoes", icon: Zap },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const collapsed = state === "collapsed";
  const { signOut, profile } = useAuth();

  const renderItems = (items: typeof mainItems) => (
    <SidebarMenu>
      {items.map((item) => (
        <SidebarMenuItem key={item.title}>
          <SidebarMenuButton asChild>
            <NavLink to={item.url} end className="hover:bg-sidebar-accent" activeClassName="bg-sidebar-accent text-sidebar-primary font-semibold">
              <item.icon className="mr-2 h-5 w-5 shrink-0" />
              {!collapsed && <span>{item.title}</span>}
            </NavLink>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        <div className={`flex items-center gap-2 ${collapsed ? 'justify-center px-2 py-4' : 'px-4 py-4'}`}>
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
            <Wrench className="h-5 w-5 text-primary-foreground" />
          </div>
          {!collapsed && <span className="font-bold text-lg text-foreground">ManutençãoPro</span>}
        </div>

        <SidebarGroup>
          <SidebarGroupLabel>Principal</SidebarGroupLabel>
          <SidebarGroupContent>{renderItems(mainItems)}</SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Gestão</SidebarGroupLabel>
          <SidebarGroupContent>{renderItems(managementItems)}</SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Serviços</SidebarGroupLabel>
          <SidebarGroupContent>{renderItems(servicesItems)}</SidebarGroupContent>
        </SidebarGroup>

        <SidebarGroup>
          <SidebarGroupLabel>Relatórios</SidebarGroupLabel>
          <SidebarGroupContent>{renderItems(reportsItems)}</SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter>
        {profile && !collapsed && (
          <div className="mx-3 mb-1 rounded-lg border border-sidebar-border bg-sidebar-accent/50 px-3 py-2.5 flex items-center gap-2">
            <div className="h-7 w-7 rounded-full bg-primary/15 flex items-center justify-center shrink-0">
              <Users className="h-3.5 w-3.5 text-primary" />
            </div>
            <p className="font-medium text-sm text-foreground truncate">{profile.nome || profile.email}</p>
          </div>
        )}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={signOut} className="text-muted-foreground hover:text-destructive hover:bg-destructive/10 justify-center">
              <LogOut className="h-4 w-4 shrink-0" />
              {!collapsed && <span>Sair</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
