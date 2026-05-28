import { createContext, useContext } from 'react';

/** Portal target element for the left config sidebar */
export const SidebarPortalCtx = createContext<HTMLElement | null>(null);

/** Returns the DOM element that page config should be portaled into */
export function useSidebarEl() {
  return useContext(SidebarPortalCtx);
}
