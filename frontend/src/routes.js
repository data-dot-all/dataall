import { lazy, Suspense } from 'react';
import AuthGuard from './components/AuthGuard';
import GuestGuard from './components/GuestGuard';
import LoadingScreen from './components/LoadingScreen';
import DefaultLayout from './components/layout/DefaultLayout';

const Loadable = (Component) => (props) =>
  (
    <Suspense fallback={<LoadingScreen />}>
      <Component {...props} />
    </Suspense>
  );

// Authentication pages
const Login = Loadable(lazy(() => import('./views/authentication/Login')));

// Error pages
const NotFound = Loadable(lazy(() => import('./views/NotFound')));

const OrganizationList = Loadable(
  lazy(() => import('./views/Organizations/OrganizationList'))
);
const OrganizationView = Loadable(
  lazy(() => import('./views/Organizations/OrganizationView'))
);
const OrganizationCreateForm = Loadable(
  lazy(() => import('./views/Organizations/OrganizationCreateForm'))
);
const OrganizationEditForm = Loadable(
  lazy(() => import('./views/Organizations/OrganizationEditForm'))
);
const EnvironmentCreateForm = Loadable(
  lazy(() => import('./views/Environments/EnvironmentCreateForm'))
);
const EnvironmentEditForm = Loadable(
  lazy(() => import('./views/Environments/EnvironmentEditForm'))
);
const EnvironmentView = Loadable(
  lazy(() => import('./views/Environments/EnvironmentView'))
);
const EnvironmentList = Loadable(
  lazy(() => import('./views/Environments/EnvironmentList'))
);
const Catalog = Loadable(lazy(() => import('./views/Catalog/Catalog')));

const DatasetList = Loadable(
  lazy(() => import('./views/Datasets/DatasetList'))
);
const DatasetView = Loadable(
  lazy(() => import('./views/Datasets/DatasetView'))
);
const DatasetCreateForm = Loadable(
  lazy(() => import('./views/Datasets/DatasetCreateForm'))
);
const DatasetImportForm = Loadable(
  lazy(() => import('./views/Datasets/DatasetImportForm'))
);
const DatasetEditForm = Loadable(
  lazy(() => import('./views/Datasets/DatasetEditForm'))
);
const TableView = Loadable(lazy(() => import('./views/Tables/TableView')));
const TableEditForm = Loadable(
  lazy(() => import('./views/Tables/TableEditForm'))
);

const FolderCreateForm = Loadable(
  lazy(() => import('./views/Folders/FolderCreateForm'))
);
const FolderView = Loadable(lazy(() => import('./views/Folders/FolderView')));
const FolderEditForm = Loadable(
  lazy(() => import('./views/Folders/FolderEditForm'))
);

const NotebookList = Loadable(
  lazy(() => import('./views/Notebooks/NotebookList'))
);
const NotebookView = Loadable(
  lazy(() => import('./views/Notebooks/NotebookView'))
);
const NotebookCreateForm = Loadable(
  lazy(() => import('./views/Notebooks/NotebookCreateForm'))
);

const MLStudioList = Loadable(
  lazy(() => import('./views/MLStudio/NotebookList'))
);
const MLStudioView = Loadable(
  lazy(() => import('./views/MLStudio/NotebookView'))
);
const MLStudioCreateForm = Loadable(
  lazy(() => import('./views/MLStudio/NotebookCreateForm'))
);

const DashboardList = Loadable(
  lazy(() => import('./views/Dashboards/DashboardList'))
);
const DashboardImportForm = Loadable(
  lazy(() => import('./views/Dashboards/DashboardImportForm'))
);
const DashboardEditForm = Loadable(
  lazy(() => import('./views/Dashboards/DashboardEditForm'))
);
const DashboardView = Loadable(
  lazy(() => import('./views/Dashboards/DashboardView'))
);
const DashboardSessionStarter = Loadable(
  lazy(() => import('./views/Dashboards/DashboardSessionStarter'))
);

const PipelineList = Loadable(
  lazy(() => import('./views/Pipelines/PipelineList'))
);
const PipelineView = Loadable(
  lazy(() => import('./views/Pipelines/PipelineView'))
);
const PipelineCreateForm = Loadable(
  lazy(() => import('./views/Pipelines/PipelineCreateForm'))
);
const PipelineEditForm = Loadable(
  lazy(() => import('./views/Pipelines/PipelineEditForm'))
);

const WarehouseCreateForm = Loadable(
  lazy(() => import('./views/Warehouses/WarehouseCreateForm'))
);
const WarehouseView = Loadable(
  lazy(() => import('./views/Warehouses/WarehouseView'))
);
const WarehouseEditForm = Loadable(
  lazy(() => import('./views/Warehouses/WarehouseEditForm'))
);
const WarehouseImportForm = Loadable(
  lazy(() => import('./views/Warehouses/WarehouseImportForm'))
);

const ShareList = Loadable(lazy(() => import('./views/Shares/ShareList')));
const ShareView = Loadable(lazy(() => import('./views/Shares/ShareView')));
const LFTagShareView = Loadable(lazy(() => import('./views/Shares/LFTagShareView')));

const WorksheetList = Loadable(
  lazy(() => import('./views/Worksheets/WorksheetList'))
);
const WorksheetView = Loadable(
  lazy(() => import('./views/Worksheets/WorksheetView'))
);
const WorksheetCreateForm = Loadable(
  lazy(() => import('./views/Worksheets/WorksheetCreateForm'))
);

const GlossaryList = Loadable(
  lazy(() => import('./views/Glossaries/GlossaryList'))
);
const GlossaryView = Loadable(
  lazy(() => import('./views/Glossaries/GlossaryView'))
);
const GlossaryCreateForm = Loadable(
  lazy(() => import('./views/Glossaries/GlossaryCreateForm'))
);

const AdministrationView = Loadable(
  lazy(() => import('./views/Administration/AdministrationView'))
);

const routes = [
  {
    children: [
      {
        path: 'login',
        element: (
          <GuestGuard>
            <Login />
          </GuestGuard>
        )
      }
    ]
  },
  {
    path: 'console',
    element: (
      <AuthGuard>
        <DefaultLayout />
      </AuthGuard>
    ),
    children: [
      {
        children: [
          {
            path: 'organizations',
            element: <OrganizationList />
          },
          {
            path: 'organizations/:uri',
            element: <OrganizationView />
          },
          {
            path: 'organizations/:uri/edit',
            element: <OrganizationEditForm />
          },
          {
            path: 'organizations/new',
            element: <OrganizationCreateForm />
          },
          {
            path: 'organizations/:uri/link',
            element: <EnvironmentCreateForm />
          }
        ]
      },
      {
        path: 'warehouse/:uri',
        element: <WarehouseView />
      },
      {
        path: 'warehouse/:uri/edit',
        element: <WarehouseEditForm />
      },
      {
        children: [
          {
            path: 'environments',
            element: <EnvironmentList />
          },
          {
            path: 'environments/:uri',
            element: <EnvironmentView />
          },
          {
            path: 'environments/:uri/edit',
            element: <EnvironmentEditForm />
          },
          {
            path: 'environments/:uri/warehouses/new',
            element: <WarehouseCreateForm />
          },
          {
            path: 'environments/:uri/warehouses/import',
            element: <WarehouseImportForm />
          }
        ]
      },
      {
        path: 'catalog',
        element: <Catalog />
      },
      {
        children: [
          {
            path: 'datasets',
            element: <DatasetList />
          },
          {
            path: 'datasets/:uri',
            element: <DatasetView />
          },
          {
            path: 'datasets/new',
            element: <DatasetCreateForm />
          },
          {
            path: 'datasets/import',
            element: <DatasetImportForm />
          },
          {
            path: 'datasets/:uri/edit',
            element: <DatasetEditForm />
          },
          {
            path: 'datasets/:uri/edit',
            element: <DatasetEditForm />
          },
          {
            path: 'datasets/table/:uri',
            element: <TableView />
          },
          {
            path: 'datasets/table/:uri/edit',
            element: <TableEditForm />
          },
          {
            path: 'datasets/:uri/newfolder',
            element: <FolderCreateForm />
          },
          {
            path: 'datasets/folder/:uri',
            element: <FolderView />
          },
          {
            path: 'datasets/folder/:uri/edit',
            element: <FolderEditForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'mlstudio',
            element: <MLStudioList />
          },
          {
            path: 'mlstudio/:uri',
            element: <MLStudioView />
          },
          {
            path: 'mlstudio/new',
            element: <MLStudioCreateForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'notebooks',
            element: <NotebookList />
          },
          {
            path: 'notebooks/:uri',
            element: <NotebookView />
          },
          {
            path: 'notebooks/new',
            element: <NotebookCreateForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'dashboards',
            element: <DashboardList />
          },
          {
            path: 'dashboards/:uri',
            element: <DashboardView />
          },
          {
            path: 'dashboards/session',
            element: <DashboardSessionStarter />
          },
          {
            path: 'dashboards/import',
            element: <DashboardImportForm />
          },
          {
            path: 'dashboards/:uri/edit',
            element: <DashboardEditForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'pipelines',
            element: <PipelineList />
          },
          {
            path: 'pipelines/:uri',
            element: <PipelineView />
          },
          {
            path: 'pipelines/new',
            element: <PipelineCreateForm />
          },
          {
            path: 'pipelines/:uri/edit',
            element: <PipelineEditForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'shares',
            element: <ShareList />
          },
          {
            path: 'shares/:uri',
            element: <ShareView />
          },
          {
            path: 'shares/lftag/:uri',
            element: <LFTagShareView />
          }
        ]
      },
      {
        children: [
          {
            path: 'worksheets',
            element: <WorksheetList />
          },
          {
            path: 'worksheets/:uri',
            element: <WorksheetView />
          },
          {
            path: 'worksheets/new',
            element: <WorksheetCreateForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'glossaries',
            element: <GlossaryList />
          },
          {
            path: 'glossaries/:uri',
            element: <GlossaryView />
          },
          {
            path: 'glossaries/new',
            element: <GlossaryCreateForm />
          }
        ]
      },
      {
        children: [
          {
            path: 'administration',
            element: <AdministrationView />
          }
        ]
      }
    ]
  },
  {
    path: '*',
    element: (
      <AuthGuard>
        <DefaultLayout />
      </AuthGuard>
    ),
    children: [
      {
        path: '',
        element: <Catalog />
      },
      {
        path: '*',
        element: <NotFound />
      }
    ]
  }
];

export default routes;
