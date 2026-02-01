import { i18n } from '@/i18n';

/**
 * 更新页面元标签（title, description, og tags等）
 */
export function updatePageMeta(title: string, description?: string, image?: string) {
  // 更新 title
  document.title = title;
  
  // 更新 meta description
  let metaDescription = document.querySelector('meta[name="description"]');
  if (!metaDescription) {
    metaDescription = document.createElement('meta');
    metaDescription.setAttribute('name', 'description');
    document.head.appendChild(metaDescription);
  }
  if (description) {
    metaDescription.setAttribute('content', description);
  }
  
  // 更新 Open Graph tags
  const updateOGTag = (property: string, content: string) => {
    let tag = document.querySelector(`meta[property="${property}"]`);
    if (!tag) {
      tag = document.createElement('meta');
      tag.setAttribute('property', property);
      document.head.appendChild(tag);
    }
    tag.setAttribute('content', content);
  };
  
  if (title) {
    updateOGTag('og:title', title);
  }
  if (description) {
    updateOGTag('og:description', description);
  }
  if (image) {
    updateOGTag('og:image', image);
  }
  
  // 更新 Twitter tags
  const updateTwitterTag = (name: string, content: string) => {
    let tag = document.querySelector(`meta[name="${name}"]`);
    if (!tag) {
      tag = document.createElement('meta');
      tag.setAttribute('name', name);
      document.head.appendChild(tag);
    }
    tag.setAttribute('content', content);
  };
  
  if (title) {
    updateTwitterTag('twitter:title', title);
  }
  if (description) {
    updateTwitterTag('twitter:description', description);
  }
  if (image) {
    updateTwitterTag('twitter:image', image);
  }
}

/**
 * 根据路由获取页面标题和描述
 */
export function getPageMeta(routeName: string, routeParams?: Record<string, any>) {
  const t = i18n.global.t;
  const baseTitle = t('app.title') || 'AxiomFlow';
  
  switch (routeName) {
    case 'landing':
      return {
        title: `${baseTitle} | ${t('landing.title')}`,
        description: t('landing.description'),
      };
    case 'dashboard':
      return {
        title: `${t('nav.documents')} | ${baseTitle}`,
        description: t('dashboard.myDocuments'),
      };
    case 'project':
      return {
        title: `${t('workbench.sourcePdf')} | ${baseTitle}`,
        description: t('workbench.sourcePdfHint'),
      };
    case 'settings':
      return {
        title: `${t('nav.settings')} | ${baseTitle}`,
        description: t('settings.title'),
      };
    case 'auth':
      return {
        title: `${t('nav.login')} | ${baseTitle}`,
        description: t('auth.loginToContinue'),
      };
    default:
      return {
        title: baseTitle,
        description: t('app.title'),
      };
  }
}

