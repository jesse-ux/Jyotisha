"use client";

import { Tooltip } from "@base-ui/react/tooltip";
import {
  createContext,
  forwardRef,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
  type ComponentProps,
  type ForwardedRef,
} from "react";

import { useSidebarViewport } from "@/hooks/use-sidebar-viewport";
import {
  defaultSidebarOpen,
  shouldHandleSidebarShortcut,
  type SidebarViewport,
} from "@/lib/sidebar-state";
import { cn } from "@/lib/utils";

export type SidebarState = "expanded" | "collapsed";

export type SidebarContextValue = {
  readonly state: SidebarState;
  readonly open: boolean;
  readonly setOpen: (open: boolean) => void;
  readonly openMobile: boolean;
  readonly setOpenMobile: (open: boolean) => void;
  readonly viewport: SidebarViewport;
  readonly ready: boolean;
  readonly isMobile: boolean;
  readonly toggleSidebar: () => void;
};

type SidebarProviderContextValue = SidebarContextValue & {
  readonly setInsetTrigger: (element: HTMLButtonElement | null) => void;
  readonly setSidebarTrigger: (element: HTMLButtonElement | null) => void;
};

export type SidebarProviderProps = ComponentProps<"div"> & {
  readonly defaultOpen?: boolean;
  readonly open?: boolean;
  readonly onOpenChange?: (open: boolean) => void;
  readonly onMobileOpenChange?: (open: boolean) => void;
  readonly escapeBlocked?: boolean;
};

export type SidebarTriggerProps = ComponentProps<"button"> & {
  readonly placement?: "inset" | "sidebar";
};

type SidebarMenuButtonProps = ComponentProps<"button"> & {
  readonly isActive?: boolean;
  readonly tooltip?: string;
};

const SidebarContext = createContext<SidebarProviderContextValue | null>(null);

function useSidebarContext(): SidebarProviderContextValue {
  const context = useContext(SidebarContext);
  if (context === null) throw new Error("Sidebar components must be used within SidebarProvider");
  return context;
}

export function useSidebar(): SidebarContextValue {
  return useSidebarContext();
}

export function SidebarProvider({
  className,
  defaultOpen = true,
  open: controlledOpen,
  onOpenChange,
  onMobileOpenChange,
  escapeBlocked = false,
  ...props
}: SidebarProviderProps) {
  const { viewport, ready } = useSidebarViewport();
  const [uncontrolledOpen, setUncontrolledOpen] = useState(defaultOpen);
  const [openMobile, setOpenMobileState] = useState(false);
  const openMobileRef = useRef(false);
  const userChangedDesktopState = useRef(false);
  const insetTriggerRef = useRef<HTMLButtonElement | null>(null);
  const sidebarTriggerRef = useRef<HTMLButtonElement | null>(null);
  const wasMobileOpen = useRef(false);
  const isControlled = controlledOpen !== undefined;
  const open = controlledOpen ?? uncontrolledOpen;
  const isMobile = viewport === "mobile";

  const setOpen = useCallback((nextOpen: boolean) => {
    userChangedDesktopState.current = true;
    if (!isControlled) setUncontrolledOpen(nextOpen);
    onOpenChange?.(nextOpen);
  }, [isControlled, onOpenChange]);

  const setOpenMobile = useCallback((nextOpen: boolean) => {
    if (openMobileRef.current === nextOpen) return;
    openMobileRef.current = nextOpen;
    setOpenMobileState(nextOpen);
    onMobileOpenChange?.(nextOpen);
  }, [onMobileOpenChange]);

  useEffect(() => {
    if (ready && !isControlled && !userChangedDesktopState.current) {
      setUncontrolledOpen(defaultSidebarOpen(viewport));
    }
  }, [isControlled, ready, viewport]);

  useEffect(() => {
    if (viewport === "mobile" || !openMobile) return;
    const closeMobileDrawer = window.requestAnimationFrame(() => setOpenMobile(false));
    return () => window.cancelAnimationFrame(closeMobileDrawer);
  }, [openMobile, setOpenMobile, viewport]);

  useEffect(() => {
    const handleKeydown = (event: KeyboardEvent) => {
      if (shouldHandleSidebarShortcut(event)) {
        event.preventDefault();
        if (isMobile) setOpenMobile(!openMobile);
        else setOpen(!open);
      }
      if (event.key === "Escape" && isMobile && openMobile && !escapeBlocked) {
        event.preventDefault();
        setOpenMobile(false);
      }
    };

    window.addEventListener("keydown", handleKeydown);
    return () => window.removeEventListener("keydown", handleKeydown);
  }, [escapeBlocked, isMobile, open, openMobile, setOpen, setOpenMobile]);

  useEffect(() => {
    if (openMobile && !wasMobileOpen.current) window.requestAnimationFrame(() => sidebarTriggerRef.current?.focus());
    if (!openMobile && wasMobileOpen.current) insetTriggerRef.current?.focus();
    wasMobileOpen.current = openMobile;
  }, [openMobile]);

  const toggleSidebar = useCallback(() => {
    if (isMobile) setOpenMobile(!openMobile);
    else setOpen(!open);
  }, [isMobile, open, openMobile, setOpen, setOpenMobile]);

  const context: SidebarProviderContextValue = {
    state: open ? "expanded" : "collapsed",
    open,
    setOpen,
    openMobile,
    setOpenMobile,
    viewport,
    ready,
    isMobile,
    toggleSidebar,
    setInsetTrigger: (element) => { insetTriggerRef.current = element; },
    setSidebarTrigger: (element) => { sidebarTriggerRef.current = element; },
  };

  return (
    <SidebarContext.Provider value={context}>
      <div
        data-mobile-open={openMobile}
        data-ready={ready}
        data-state={context.state}
        data-viewport={viewport}
        className={cn("group/sidebar-provider flex min-h-0 w-full", className)}
        {...props}
      />
    </SidebarContext.Provider>
  );
}

export function Sidebar({ id, className, ...props }: ComponentProps<"aside">) {
  const { isMobile, open, openMobile, setOpenMobile } = useSidebar();
  return <>
    <button type="button" data-sidebar="scrim" data-slot="sidebar-scrim" data-mobile-open={isMobile && openMobile} aria-label="关闭聊天记录" aria-hidden={!isMobile || !openMobile} tabIndex={isMobile && openMobile ? 0 : -1} className="sidebar-scrim" onClick={() => setOpenMobile(false)} />
    <aside id={id ?? "chat-sidebar"} data-sidebar="sidebar" data-slot="sidebar" data-state={open ? "expanded" : "collapsed"} data-mobile-open={openMobile} className={cn("flex min-h-0 shrink-0 flex-col", className)} {...props} />
  </>;
}

export function SidebarHeader({ className, ...props }: ComponentProps<"div">) {
  return <div data-sidebar="header" data-slot="sidebar-header" className={cn("shrink-0", className)} {...props} />;
}

export function SidebarContent({ className, ...props }: ComponentProps<"div">) {
  return <div data-sidebar="content" data-slot="sidebar-content" className={cn("min-h-0 flex-1 overflow-y-auto", className)} {...props} />;
}

export function SidebarGroup({ className, ...props }: ComponentProps<"section">) {
  return <section data-sidebar="group" data-slot="sidebar-group" className={cn("min-w-0", className)} {...props} />;
}

export function SidebarGroupLabel({ className, ...props }: ComponentProps<"h2">) {
  return <h2 data-sidebar="group-label" data-slot="sidebar-group-label" className={cn("min-h-11", className)} {...props} />;
}

export function SidebarGroupContent({ className, ...props }: ComponentProps<"div">) {
  return <div data-sidebar="group-content" data-slot="sidebar-group-content" className={cn("min-w-0", className)} {...props} />;
}

export function SidebarMenu({ className, ...props }: ComponentProps<"ul">) {
  return <ul data-sidebar="menu" data-slot="sidebar-menu" className={cn("grid min-w-0 gap-1", className)} {...props} />;
}

export function SidebarMenuItem({ className, ...props }: ComponentProps<"li">) {
  return <li data-sidebar="menu-item" data-slot="sidebar-menu-item" className={cn("min-w-0", className)} {...props} />;
}

export function SidebarMenuButton({ className, isActive = false, tooltip, ...props }: SidebarMenuButtonProps) {
  const { isMobile, state } = useSidebar();
  const button = <button data-sidebar="menu-button" data-slot="sidebar-menu-button" data-active={isActive} className={cn("min-h-11 w-full", className)} {...props} />;
  if (tooltip === undefined || state !== "collapsed" || isMobile) return button;
  return <Tooltip.Root><Tooltip.Trigger render={button} /><Tooltip.Portal><Tooltip.Positioner side="right" sideOffset={8}><Tooltip.Popup>{tooltip}</Tooltip.Popup></Tooltip.Positioner></Tooltip.Portal></Tooltip.Root>;
}

export function SidebarFooter({ className, ...props }: ComponentProps<"div">) {
  return <div data-sidebar="footer" data-slot="sidebar-footer" className={cn("shrink-0", className)} {...props} />;
}

export function SidebarInset({ className, inert, ...props }: ComponentProps<"section">) {
  const { isMobile, openMobile } = useSidebar();
  return <section data-sidebar="inset" data-slot="sidebar-inset" inert={Boolean(inert) || (isMobile && openMobile)} className={cn("min-w-0 flex-1", className)} {...props} />;
}

function setRef(ref: ForwardedRef<HTMLButtonElement>, element: HTMLButtonElement | null): void {
  if (typeof ref === "function") ref(element);
  else if (ref !== null) ref.current = element;
}

export const SidebarTrigger = forwardRef<HTMLButtonElement, SidebarTriggerProps>(function SidebarTrigger({
  placement = "inset",
  className,
  onClick,
  ...props
}, ref) {
  const { isMobile, open, openMobile, setInsetTrigger, setSidebarTrigger, toggleSidebar } = useSidebarContext();
  const expanded = isMobile ? openMobile : open;
  const label = isMobile
    ? openMobile ? "关闭聊天记录" : "打开聊天记录"
    : open ? "收起侧边栏" : "展开侧边栏";
  const register = (element: HTMLButtonElement | null) => {
    setRef(ref, element);
    if (placement === "inset") setInsetTrigger(element);
    else setSidebarTrigger(element);
  };
  return <button ref={register} type="button" data-sidebar="trigger" data-slot="sidebar-trigger" aria-label={label} aria-expanded={expanded} className={cn("min-h-11 min-w-11", className)} onClick={(event) => { onClick?.(event); if (!event.defaultPrevented) toggleSidebar(); }} {...props} />;
});

export function SidebarRail({ className, onClick, ...props }: ComponentProps<"button">) {
  const { isMobile, open, setOpen } = useSidebar();
  if (isMobile) return null;
  const label = open ? "Collapse sidebar" : "Expand sidebar";
  return <button type="button" data-sidebar="rail" data-slot="sidebar-rail" aria-label={label} className={cn("min-h-11 min-w-11", className)} onClick={(event) => { onClick?.(event); if (!event.defaultPrevented) setOpen(!open); }} {...props} />;
}
