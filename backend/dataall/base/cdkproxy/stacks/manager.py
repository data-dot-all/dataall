from tabulate import tabulate
import logging

logger = logging.getLogger('cdksass')


class StackManagerFactory:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.stacks = {}

    def register_stack(self, stack):
        def decorator(cls):
            self.stacks[stack] = cls
            return cls

        return decorator

    def instanciate_stack(self, stack, scope, id, **kwargs):
        if stack in self.stacks.keys():
            cls = self.stacks[stack]
            logger.info(f'instanciating task with  scope {scope}, id {id}, args {str(kwargs)}')
            return cls(scope, id, **kwargs)
        else:
            logger.warning(f'Could not find stack {stack}')
        raise Exception(f'Unknown stack type `{stack}`')

    def registered_stacks(self):
        logger.info('Registered Stacks :')
        table = [[stack, self.stacks[stack].module_name] for stack in self.stacks.keys()]
        tbl = tabulate(table, headers=['StackType', 'Module'], tablefmt='simple')
        logger.info(f'\n {tbl}')
        return self.stacks


stack = StackManagerFactory.get_instance().register_stack
instanciate_stack = StackManagerFactory.get_instance().instanciate_stack
StackManager = StackManagerFactory.get_instance()
