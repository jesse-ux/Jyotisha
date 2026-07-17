"use client";

import { useEffect, useState } from "react";

import { sidebarViewportForWidth, type SidebarViewport } from "@/lib/sidebar-state";

type SidebarViewportState = {
  readonly viewport: SidebarViewport;
  readonly ready: boolean;
};

const initialViewportState: SidebarViewportState = {
  viewport: "desktop",
  ready: false,
};

export function useSidebarViewport(): SidebarViewportState {
  const [state, setState] = useState(initialViewportState);

  useEffect(() => {
    const updateViewport = () => {
      setState({ viewport: sidebarViewportForWidth(window.innerWidth), ready: true });
    };

    updateViewport();
    window.addEventListener("resize", updateViewport);
    return () => window.removeEventListener("resize", updateViewport);
  }, []);

  return state;
}
