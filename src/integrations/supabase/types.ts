export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  // Allows to automatically instantiate createClient with right options
  // instead of createClient<Database, { PostgrestVersion: 'XX' }>(URL, KEY)
  __InternalSupabase: {
    PostgrestVersion: "14.4"
  }
  public: {
    Tables: {
      colaboradores: {
        Row: {
          area: string
          cargo: string | null
          created_at: string | null
          id: string
          nome: string
          status: string | null
          turno: string
          updated_at: string | null
        }
        Insert: {
          area: string
          cargo?: string | null
          created_at?: string | null
          id?: string
          nome: string
          status?: string | null
          turno: string
          updated_at?: string | null
        }
        Update: {
          area?: string
          cargo?: string | null
          created_at?: string | null
          id?: string
          nome?: string
          status?: string | null
          turno?: string
          updated_at?: string | null
        }
        Relationships: []
      }
      equipamentos: {
        Row: {
          area: string | null
          created_at: string | null
          equipamento: string
          id: string
          local: string | null
          status: string | null
          tag: string | null
          updated_at: string | null
        }
        Insert: {
          area?: string | null
          created_at?: string | null
          equipamento: string
          id?: string
          local?: string | null
          status?: string | null
          tag?: string | null
          updated_at?: string | null
        }
        Update: {
          area?: string | null
          created_at?: string | null
          equipamento?: string
          id?: string
          local?: string | null
          status?: string | null
          tag?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      ocorrencias: {
        Row: {
          area: string
          area_responsavel: string | null
          colaborador_id: string | null
          created_at: string | null
          created_by: string | null
          data_ocorrencia: string
          descricao: string
          equipamento: string | null
          gerar_os: boolean | null
          horario: string
          houve_parada: boolean | null
          id: string
          local: string | null
          numero_os: string | null
          observacao_os: string | null
          prioridade_os: string | null
          status: string | null
          status_integracao_os: string | null
          tag: string | null
          tempo_parada: string | null
          tipo_manutencao_os: string | null
          tipo_ocorrencia: string | null
          tipo_parada: string | null
          turno: string
          updated_at: string | null
        }
        Insert: {
          area: string
          area_responsavel?: string | null
          colaborador_id?: string | null
          created_at?: string | null
          created_by?: string | null
          data_ocorrencia: string
          descricao: string
          equipamento?: string | null
          gerar_os?: boolean | null
          horario: string
          houve_parada?: boolean | null
          id?: string
          local?: string | null
          numero_os?: string | null
          observacao_os?: string | null
          prioridade_os?: string | null
          status?: string | null
          status_integracao_os?: string | null
          tag?: string | null
          tempo_parada?: string | null
          tipo_manutencao_os?: string | null
          tipo_ocorrencia?: string | null
          tipo_parada?: string | null
          turno: string
          updated_at?: string | null
        }
        Update: {
          area?: string
          area_responsavel?: string | null
          colaborador_id?: string | null
          created_at?: string | null
          created_by?: string | null
          data_ocorrencia?: string
          descricao?: string
          equipamento?: string | null
          gerar_os?: boolean | null
          horario?: string
          houve_parada?: boolean | null
          id?: string
          local?: string | null
          numero_os?: string | null
          observacao_os?: string | null
          prioridade_os?: string | null
          status?: string | null
          status_integracao_os?: string | null
          tag?: string | null
          tempo_parada?: string | null
          tipo_manutencao_os?: string | null
          tipo_ocorrencia?: string | null
          tipo_parada?: string | null
          turno?: string
          updated_at?: string | null
        }
        Relationships: [
          {
            foreignKeyName: "ocorrencias_colaborador_id_fkey"
            columns: ["colaborador_id"]
            isOneToOne: false
            referencedRelation: "colaboradores"
            referencedColumns: ["id"]
          },
        ]
      }
      ocorrencias_importacao: {
        Row: {
          area: string | null
          colaborador_id_match: string | null
          created_at: string | null
          data_ocorrencia: string
          descricao_original: string | null
          equipamento_id_match: string | null
          equipamento_original: string | null
          horario: string | null
          id: string
          local_original: string | null
          match_por_tag: boolean | null
          observacao_importacao: string | null
          responsavel_original: string | null
          status_original: string | null
          tag_original: string | null
          tempo_parada_min: number | null
          tempo_parada_original: string | null
          tipo_servico_original: string | null
          turno: string | null
        }
        Insert: {
          area?: string | null
          colaborador_id_match?: string | null
          created_at?: string | null
          data_ocorrencia: string
          descricao_original?: string | null
          equipamento_id_match?: string | null
          equipamento_original?: string | null
          horario?: string | null
          id?: string
          local_original?: string | null
          match_por_tag?: boolean | null
          observacao_importacao?: string | null
          responsavel_original?: string | null
          status_original?: string | null
          tag_original?: string | null
          tempo_parada_min?: number | null
          tempo_parada_original?: string | null
          tipo_servico_original?: string | null
          turno?: string | null
        }
        Update: {
          area?: string | null
          colaborador_id_match?: string | null
          created_at?: string | null
          data_ocorrencia?: string
          descricao_original?: string | null
          equipamento_id_match?: string | null
          equipamento_original?: string | null
          horario?: string | null
          id?: string
          local_original?: string | null
          match_por_tag?: boolean | null
          observacao_importacao?: string | null
          responsavel_original?: string | null
          status_original?: string | null
          tag_original?: string | null
          tempo_parada_min?: number | null
          tempo_parada_original?: string | null
          tipo_servico_original?: string | null
          turno?: string | null
        }
        Relationships: []
      }
      profiles: {
        Row: {
          area: string | null
          created_at: string | null
          email: string | null
          id: string
          nome: string | null
          perfil: string | null
          updated_at: string | null
        }
        Insert: {
          area?: string | null
          created_at?: string | null
          email?: string | null
          id: string
          nome?: string | null
          perfil?: string | null
          updated_at?: string | null
        }
        Update: {
          area?: string | null
          created_at?: string | null
          email?: string | null
          id?: string
          nome?: string | null
          perfil?: string | null
          updated_at?: string | null
        }
        Relationships: []
      }
      user_roles: {
        Row: {
          id: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Insert: {
          id?: string
          role: Database["public"]["Enums"]["app_role"]
          user_id: string
        }
        Update: {
          id?: string
          role?: Database["public"]["Enums"]["app_role"]
          user_id?: string
        }
        Relationships: []
      }
    }
    Views: {
      vw_equipamentos_app: {
        Row: {
          area: string | null
          equipamento: string | null
          local: string | null
          status: string | null
          tag: string | null
          updated_at: string | null
        }
        Relationships: []
      }
      vw_equipamentos_consolidados: {
        Row: {
          area: string | null
          equipamento: string | null
          local_exemplo: string | null
          qtd_registros_origem: number | null
          status: string | null
          tag: string | null
          updated_at: string | null
        }
        Relationships: []
      }
      vw_equipamentos_mapeados: {
        Row: {
          area: string | null
          consolidado_no_pai: boolean | null
          created_at: string | null
          equipamento: string | null
          equipamento_representacao: string | null
          id: string | null
          local: string | null
          status: string | null
          tag: string | null
          tag_representacao: string | null
          updated_at: string | null
        }
        Relationships: []
      }
      vw_equipamentos_tratados: {
        Row: {
          area: string | null
          codigo_da_tag: string | null
          codigo_no_grupo: string | null
          codigo_principal: string | null
          cp_no_local: string | null
          created_at: string | null
          eh_instrumentacao: boolean | null
          eh_sensor: boolean | null
          equipamento: string | null
          grupo_principal: string | null
          id: string | null
          local: string | null
          prefixo_tag: string | null
          status: string | null
          tag: string | null
          tipo_registro_final: string | null
          updated_at: string | null
        }
        Relationships: []
      }
    }
    Functions: {
      get_user_area: { Args: { _user_id: string }; Returns: string }
      has_role: {
        Args: {
          _role: Database["public"]["Enums"]["app_role"]
          _user_id: string
        }
        Returns: boolean
      }
    }
    Enums: {
      app_role: "administrador" | "manutencao_eletrica" | "manutencao_mecanica"
    }
    CompositeTypes: {
      [_ in never]: never
    }
  }
}

type DatabaseWithoutInternals = Omit<Database, "__InternalSupabase">

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, "public">]

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema["Tables"] & DefaultSchema["Views"])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Views"])[TableName] extends {
      Row: infer R
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema["Tables"] &
        DefaultSchema["Views"])
    ? (DefaultSchema["Tables"] &
        DefaultSchema["Views"])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R
      }
      ? R
      : never
    : never

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Insert: infer I
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I
      }
      ? I
      : never
    : never

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema["Tables"]
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"]
    : never = never,
> = DefaultSchemaTableNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions["schema"]]["Tables"][TableName] extends {
      Update: infer U
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema["Tables"]
    ? DefaultSchema["Tables"][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U
      }
      ? U
      : never
    : never

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema["Enums"]
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"]
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions["schema"]]["Enums"][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema["Enums"]
    ? DefaultSchema["Enums"][DefaultSchemaEnumNameOrOptions]
    : never

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema["CompositeTypes"]
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"]
    : never = never,
> = PublicCompositeTypeNameOrOptions extends {
  schema: keyof DatabaseWithoutInternals
}
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions["schema"]]["CompositeTypes"][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema["CompositeTypes"]
    ? DefaultSchema["CompositeTypes"][PublicCompositeTypeNameOrOptions]
    : never

export const Constants = {
  public: {
    Enums: {
      app_role: ["administrador", "manutencao_eletrica", "manutencao_mecanica"],
    },
  },
} as const
