import type { ComponentInstance, MenuCustomization } from '../../contracts/generated/customization';

export interface EditorCommand {
  type: string;
  execute(config: MenuCustomization): MenuCustomization;
}

export class SetThemeCommand implements EditorCommand {
  type = 'SET_THEME';
  constructor(public themeId: string, public version: string = '1.0.0') {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      theme: {
        ...config.theme,
        id: this.themeId,
        version: this.version,
      },
    };
  }
}

export class SetTokenOverrideCommand implements EditorCommand {
  type = 'SET_TOKEN_OVERRIDE';
  constructor(public path: string, public value: any) {}

  execute(config: MenuCustomization): MenuCustomization {
    const copy = JSON.parse(JSON.stringify(config)) as MenuCustomization;
    const parts = this.path.split('.');
    let curr: any = copy.theme.overrides;
    for (let i = 0; i < parts.length - 1; i++) {
      if (!curr[parts[i]]) curr[parts[i]] = {};
      curr = curr[parts[i]];
    }
    curr[parts[parts.length - 1]] = this.value;
    return copy;
  }
}

export class SetLayoutCommand implements EditorCommand {
  type = 'SET_LAYOUT';
  constructor(public layoutId: string, public version: string = '1.0.0') {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      layout: {
        ...config.layout,
        id: this.layoutId,
        version: this.version,
      },
    };
  }
}

export class SetLayoutSettingCommand implements EditorCommand {
  type = 'SET_LAYOUT_SETTING';
  constructor(public key: string, public value: any) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      layout: {
        ...config.layout,
        settings: {
          ...config.layout.settings,
          [this.key]: this.value,
        },
      },
    };
  }
}

export class AddComponentCommand implements EditorCommand {
  type = 'ADD_COMPONENT';
  constructor(public instance: ComponentInstance) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      components: [...config.components, this.instance],
    };
  }
}

export class RemoveComponentCommand implements EditorCommand {
  type = 'REMOVE_COMPONENT';
  constructor(public instanceId: string) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      components: config.components.filter((c) => c.id !== this.instanceId),
    };
  }
}

export class ReorderComponentCommand implements EditorCommand {
  type = 'REORDER_COMPONENT';
  constructor(public instanceId: string, public newOrder: number) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      components: config.components.map((c) =>
        c.id === this.instanceId ? { ...c, order: this.newOrder } : c
      ),
    };
  }
}

export class UpdateComponentPropsCommand implements EditorCommand {
  type = 'UPDATE_COMPONENT_PROPS';
  constructor(public instanceId: string, public newProps: Record<string, any>) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      components: config.components.map((c) =>
        c.id === this.instanceId ? { ...c, props: { ...c.props, ...this.newProps } } : c
      ),
    };
  }
}

export class SetComponentVisibilityCommand implements EditorCommand {
  type = 'SET_COMPONENT_VISIBILITY';
  constructor(public instanceId: string, public visible: boolean) {}

  execute(config: MenuCustomization): MenuCustomization {
    return {
      ...config,
      components: config.components.map((c) =>
        c.id === this.instanceId ? { ...c, visible: this.visible } : c
      ),
    };
  }
}
