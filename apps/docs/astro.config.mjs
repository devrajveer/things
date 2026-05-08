import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  integrations: [
    starlight({
      title: 'MegaIoT Documentation',
      social: {
        github: 'https://github.com/your-org/your-repo',
      },
      sidebar: [
        {
          label: 'Start Here',
          items: [
            { label: 'Introduction', link: '/' },
            { label: 'Getting Started', link: '/getting-started/' },
          ],
        },
        {
          label: 'Concepts',
          items: [
            { label: 'Architecture', link: '/concepts/architecture/' },
          ],
        },
      ],
      customCss: [],
    }),
  ],
});
