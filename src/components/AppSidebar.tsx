import {
  LayoutDashboard, FileText, History, Users, Wrench, BarChart3, Zap, LogOut, Settings
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
          <SidebarGroupLabel>Relatórios</SidebarGroupLabel>
          <SidebarGroupContent>{renderItems(reportsItems)}</SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>

      <SidebarFooter className="p-3">
        {profile && !collapsed && (
          <div className="mb-2 rounded-lg bg-primary/10 border border-primary/20 p-3">
            <p className="font-semibold text-sm text-foreground truncate">{profile.nome || profile.email}</p>
          </div>
        )}
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton onClick={signOut} className={`text-destructive hover:bg-destructive/10 ${collapsed ? 'justify-center' : ''}`}>
              <LogOut className={`h-5 w-5 ${collapsed ? '' : 'mr-2'}`} />
              {!collapsed && <span>Sair</span>}
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
