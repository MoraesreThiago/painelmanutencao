const SIDEBAR_COLLAPSED_COOKIE = "sgm_sidebar_collapsed"
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 365
const SELECTORS = {
  shell: "[data-sidebar-shell]",
  toggle: "[data-sidebar-toggle]",
  navLinks: "[data-sidebar-link]",
  profileMenu: "[data-profile-menu]",
  profileTrigger: "[data-profile-trigger]",
  profilePanel: "[data-profile-panel]",
}

document.addEventListener("htmx:responseError", (event) => {
  console.error("HTMX error", {
    status: event.detail.xhr?.status,
    statusText: event.detail.xhr?.statusText,
    path: event.detail.pathInfo?.requestPath,
  })
})

const assistantWorkspaceSelector = "#assistant-workspace"
const burnedCaseFormSelector = "[data-burned-case-form]"

const getPromptField = () => document.querySelector("textarea[name='prompt']")

const bindAssistantUI = (scope = document) => {
  const workspace = scope.matches?.(assistantWorkspaceSelector)
    ? scope
    : scope.querySelector?.(assistantWorkspaceSelector)

  document.querySelectorAll("[data-chat-prompt]").forEach((button) => {
    if (button.dataset.chatPromptBound === "true") {
      return
    }

    button.dataset.chatPromptBound = "true"
    button.addEventListener("click", () => {
      const promptField = getPromptField()
      if (!promptField) {
        return
      }

      promptField.value = button.dataset.chatPrompt || ""
      promptField.focus()
      promptField.setSelectionRange(promptField.value.length, promptField.value.length)
    })
  })

  const thread = workspace?.querySelector?.("#assistant-thread") || document.querySelector("#assistant-thread")
  if (thread) {
    thread.scrollTop = thread.scrollHeight
  }
}

const bindBurnedCaseForm = (scope = document) => {
  const form = scope.matches?.(burnedCaseFormSelector)
    ? scope
    : scope.querySelector?.(burnedCaseFormSelector)

  if (!form || form.dataset.burnedCaseBound === "true") {
    return
  }

  form.dataset.burnedCaseBound = "true"

  const catalogScript = document.getElementById("burned-motor-catalog")
  const select = form.querySelector("select[name='motor_lookup']")
  const filterInput = form.querySelector("[data-burned-case-motor-filter]")
  const sourceLabel = form.querySelector("[data-burned-case-source]")

  if (!select || !catalogScript) {
    return
  }

  let catalog = {}
  try {
    catalog = JSON.parse(catalogScript.textContent || "{}")
  } catch (error) {
    console.error("Nao foi possivel carregar o catalogo de motores", error)
    return
  }

  const fieldSelectors = {
    unidade: "select[name='unidade']",
    motor_description: "input[name='motor_description']",
    motor_mo: "input[name='motor_mo']",
    motor_power: "input[name='motor_power']",
    motor_manufacturer: "input[name='motor_manufacturer']",
    motor_frame: "input[name='motor_frame']",
    motor_rpm: "input[name='motor_rpm']",
    motor_voltage: "input[name='motor_voltage']",
    motor_current: "input[name='motor_current']",
    motor_location: "input[name='motor_location']",
  }

  const fields = Object.fromEntries(
    Object.entries(fieldSelectors).map(([key, selector]) => [key, form.querySelector(selector)])
  )

  const originalOptions = [...select.options].map((option) => ({
    value: option.value,
    text: option.text,
    selected: option.selected,
  }))

  const updateSourceLabel = () => {
    if (!sourceLabel) {
      return
    }

    sourceLabel.textContent = select.value
      ? "Dados reaproveitados do cadastro"
      : "Preenchimento manual"
  }

  const applySnapshot = () => {
    const snapshot = catalog[select.value]
    if (!snapshot) {
      updateSourceLabel()
      return
    }

    Object.entries(fields).forEach(([key, field]) => {
      if (!field) {
        return
      }

      if (key === "unidade") {
        if (snapshot[key]) {
          field.value = snapshot[key]
        }
        return
      }

      field.value = snapshot[key] ?? ""
    })

    updateSourceLabel()
  }

  const rebuildOptions = (query) => {
    const normalized = query.trim().toLowerCase()
    const selectedValue = select.value
    const nextOptions = originalOptions.filter((option, index) => {
      if (index === 0 || !normalized || option.value === selectedValue) {
        return true
      }
      return option.text.toLowerCase().includes(normalized)
    })

    select.innerHTML = ""
    nextOptions.forEach((option) => {
      const nextOption = document.createElement("option")
      nextOption.value = option.value
      nextOption.textContent = option.text
      nextOption.selected = option.value === selectedValue
      select.appendChild(nextOption)
    })
  }

  select.addEventListener("change", applySnapshot)

  if (filterInput) {
    filterInput.addEventListener("input", () => {
      rebuildOptions(filterInput.value)
    })
  }

  if (select.value) {
    applySnapshot()
  } else {
    updateSourceLabel()
  }
}

const readCookie = (name) => {
  const value = document.cookie
    .split("; ")
    .find((cookie) => cookie.startsWith(`${name}=`))

  return value ? decodeURIComponent(value.split("=").slice(1).join("=")) : null
}

const writeCookie = (name, value, maxAge) => {
  document.cookie = `${name}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`
}

const bindFlashMessages = (scope = document) => {
  scope.querySelectorAll?.("[data-flash-timeout]").forEach((flash) => {
    if (flash.dataset.flashBound === "true") {
      return
    }

    flash.dataset.flashBound = "true"
    const timeout = Number.parseInt(flash.dataset.flashTimeout || "", 10)
    if (!Number.isFinite(timeout) || timeout <= 0) {
      return
    }

    window.setTimeout(() => {
      flash.classList.add("is-dismissing")
      window.setTimeout(() => {
        flash.remove()
      }, 180)
    }, timeout)
  })
}

const closeCustomSelects = (except = null) => {
  document.querySelectorAll("[data-custom-select].is-open").forEach((wrapper) => {
    if (except && wrapper === except) {
      return
    }

    wrapper.classList.remove("is-open")
    const profilePanel = wrapper.closest("[data-profile-panel]")
    if (profilePanel) {
      profilePanel.classList.remove("is-select-open")
      delete profilePanel.dataset.openSelect
    }
    const trigger = wrapper.querySelector(".sidebar-custom-select-trigger")
    const menu = wrapper.querySelector(".sidebar-custom-select-menu")
    if (trigger) {
      trigger.setAttribute("aria-expanded", "false")
    }
    if (menu) {
      menu.hidden = true
    }
  })
}

const bindCustomSelects = (scope = document) => {
  scope.querySelectorAll?.("[data-custom-select]").forEach((wrapper) => {
    if (wrapper.dataset.customSelectBound === "true") {
      return
    }

    const select = wrapper.querySelector("select")
    if (!select) {
      return
    }

    wrapper.dataset.customSelectBound = "true"
    wrapper.classList.add("is-enhanced")
    wrapper.dataset.selectName = select.name

    const hiddenInput = document.createElement("input")
    hiddenInput.type = "hidden"
    hiddenInput.name = select.name
    hiddenInput.value = select.value
    wrapper.appendChild(hiddenInput)

    select.removeAttribute("name")
    select.tabIndex = -1
    select.setAttribute("aria-hidden", "true")

    const trigger = document.createElement("button")
    trigger.type = "button"
    trigger.className = "sidebar-custom-select-trigger"
    trigger.setAttribute("aria-haspopup", "listbox")
    trigger.setAttribute("aria-expanded", "false")

    const triggerLabel = document.createElement("span")
    triggerLabel.className = "sidebar-custom-select-label"

    const triggerCaret = document.createElement("span")
    triggerCaret.className = "sidebar-custom-select-caret"
    triggerCaret.setAttribute("aria-hidden", "true")

    trigger.append(triggerLabel, triggerCaret)

    const menu = document.createElement("div")
    menu.className = "sidebar-custom-select-menu"
    menu.setAttribute("role", "listbox")
    menu.hidden = true

    const syncTriggerLabel = () => {
      const selectedOption = select.options[select.selectedIndex]
      triggerLabel.textContent = selectedOption?.text || "Selecionar"
    }

    const renderOptions = () => {
      menu.replaceChildren()

      Array.from(select.options).forEach((option) => {
        const item = document.createElement("button")
        item.type = "button"
        item.className = "sidebar-custom-select-option"
        item.textContent = option.text
        item.setAttribute("role", "option")

        if (option.disabled) {
          item.disabled = true
        }

        if (option.selected) {
          item.classList.add("is-selected")
          item.setAttribute("aria-selected", "true")
        } else {
          item.setAttribute("aria-selected", "false")
        }

        item.addEventListener("click", () => {
          if (option.disabled) {
            return
          }

          select.value = option.value
          hiddenInput.value = option.value
          select.dispatchEvent(new Event("change", { bubbles: true }))
          syncTriggerLabel()
          renderOptions()
          closeCustomSelects()
          trigger.focus()
        })

        menu.appendChild(item)
      })
    }

    trigger.addEventListener("click", (event) => {
      event.preventDefault()
      const isOpen = wrapper.classList.contains("is-open")
      closeCustomSelects(wrapper)
      wrapper.classList.toggle("is-open", !isOpen)
      const profilePanel = wrapper.closest("[data-profile-panel]")
      if (profilePanel) {
        profilePanel.classList.toggle("is-select-open", !isOpen)
        if (!isOpen) {
          profilePanel.dataset.openSelect = wrapper.dataset.selectName || ""
        } else {
          delete profilePanel.dataset.openSelect
        }
      }
      trigger.setAttribute("aria-expanded", (!isOpen).toString())
      menu.hidden = isOpen
    })

    select.addEventListener("change", () => {
      syncTriggerLabel()
      renderOptions()
    })

    wrapper.append(trigger, menu)
    syncTriggerLabel()
    renderOptions()
  })
}

document.addEventListener("DOMContentLoaded", () => {
  bindAssistantUI()
  bindBurnedCaseForm()
  bindFlashMessages()
  bindCustomSelects()
  document.body.addEventListener("htmx:afterSwap", (event) => {
    bindAssistantUI(event.target)
    bindBurnedCaseForm(event.target)
    bindFlashMessages(event.target)
    bindCustomSelects(event.target)
  })

  const shell = document.querySelector(SELECTORS.shell)
  const toggle = shell?.querySelector(SELECTORS.toggle)
  const profileMenu = shell?.querySelector(SELECTORS.profileMenu)
  const profileTrigger = shell?.querySelector(SELECTORS.profileTrigger)
  const profilePanel = shell?.querySelector(SELECTORS.profilePanel)
  const sidebarLinks = shell ? [...shell.querySelectorAll(SELECTORS.navLinks)] : []

  if (!shell || !toggle) {
    return
  }

  const syncSidebarTooltips = (collapsed) => {
    sidebarLinks.forEach((link) => {
      const tooltip = link.dataset.sidebarTooltip
      if (!tooltip) {
        return
      }

      if (collapsed) {
        link.setAttribute("title", tooltip)
        return
      }

      link.removeAttribute("title")
    })

    const profileTooltip = profileTrigger?.dataset.sidebarTooltip
    if (!profileTrigger || !profileTooltip) {
      return
    }

    if (collapsed) {
      profileTrigger.setAttribute("title", profileTooltip)
      return
    }

    profileTrigger.removeAttribute("title")
  }

  const applySidebarState = (collapsed) => {
    shell.classList.toggle("is-sidebar-collapsed", collapsed)
    toggle.setAttribute("aria-expanded", (!collapsed).toString())

    const toggleLabel = collapsed ? "Expandir menu lateral" : "Recolher menu lateral"
    toggle.setAttribute("aria-label", toggleLabel)
    toggle.setAttribute("title", toggleLabel)
    syncSidebarTooltips(collapsed)
  }

  const closeProfileMenu = () => {
    if (!profileMenu || !profileTrigger || !profilePanel) {
      return
    }

    closeCustomSelects()
    profileMenu.classList.remove("is-open")
    profileTrigger.setAttribute("aria-expanded", "false")
    profileTrigger.setAttribute("aria-label", "Abrir menu do usuário")
    profilePanel.hidden = true
    profilePanel.setAttribute("aria-hidden", "true")
  }

  const toggleProfileMenu = () => {
    if (!profileMenu || !profileTrigger || !profilePanel) {
      return
    }

    const isOpen = profileMenu.classList.toggle("is-open")
    profileTrigger.setAttribute("aria-expanded", isOpen.toString())
    profileTrigger.setAttribute("aria-label", isOpen ? "Fechar menu do usuário" : "Abrir menu do usuário")
    profilePanel.hidden = !isOpen
    profilePanel.setAttribute("aria-hidden", (!isOpen).toString())
  }

  const persistedState = readCookie(SIDEBAR_COLLAPSED_COOKIE)
  const isInitiallyCollapsed = persistedState === null
    ? shell.classList.contains("is-sidebar-collapsed")
    : persistedState === "true"

  applySidebarState(isInitiallyCollapsed)
  window.requestAnimationFrame(() => {
    shell.classList.add("is-sidebar-ready")
  })

  toggle.addEventListener("click", () => {
    const collapsed = !shell.classList.contains("is-sidebar-collapsed")
    applySidebarState(collapsed)
    writeCookie(SIDEBAR_COLLAPSED_COOKIE, collapsed.toString(), SIDEBAR_COOKIE_MAX_AGE)
    closeProfileMenu()
  })

  if (profileTrigger && profilePanel && profileMenu) {
    profileTrigger.addEventListener("click", (event) => {
      event.stopPropagation()
      toggleProfileMenu()
    })

    profilePanel.addEventListener("click", (event) => {
      event.stopPropagation()
      if (!(event.target instanceof Element) || !event.target.closest("[data-custom-select]")) {
        closeCustomSelects()
      }
    })

    document.addEventListener("click", (event) => {
      if (!profileMenu.contains(event.target)) {
        closeProfileMenu()
      }
    })

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        closeProfileMenu()
      }
    })
  }

  document.addEventListener("click", (event) => {
    if (!(event.target instanceof Element) || !event.target.closest("[data-custom-select]")) {
      closeCustomSelects()
    }
  })
})
