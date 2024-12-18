class General_Customer:
    def __init__(self, name, customer_id, university, customer_type, discount=0):
        assert discount>=0 and discount<=100, "Discount should be between 0 and 100"
        assert isinstance(university, University), "university should be of type University"
        self.name = name
        self.customer_id = customer_id
        self.university = university
        self.customer_type = customer_type
        self.discount = discount
        self.balance = 0
        self.orders = []
    
    def __str__(self):
        if self.customer_id == None:
            return f"{self.name} ({self.customer_type})"   
        else:
            return f"{self.name} - {self.customer_id} ({self.customer_type})"    
        
    def __repr__(self):
        return self.__str__()
    
    def view_menu(self, cafeteria_name):
        """Lets the customer view the menu of a cafeteria and the prices of the items after applying the discount.

        Args:
            cafeteria_name (String): the cafeteria name whose menu the customer wants to view

        Returns:
            dict: A dictionary with item names as keys and a tuple of price after discount and quantity available as values.
        """
        cafeteria = self.university.get_cafeteria(cafeteria_name)
        assert cafeteria != None, f"Sorry, {cafeteria_name} is not available in the university"
        menu_with_discount = {}
        for item, details in cafeteria.menu.items():
            discounted_price = details['price'] * (1 - (self.discount / 100))
            menu_with_discount[item] = (discounted_price, details['quantity'])
        return menu_with_discount
    
    def view_detailed_menu(self, cafeteria_name):
        """Lets the customer view the detailed menu of a cafeteria.

        Args:
            cafeteria_name (String): the cafeteria name whose menu the customer wants to view

        Returns:
            dict: A dictionary with item names as keys and a tuple of description, price after discount, and quantity available as values.
        """
        cafeteria = self.university.get_cafeteria(cafeteria_name)
        assert cafeteria != None, f"Sorry, {cafeteria_name} is not available in the university"
        detailed_menu = {}
        for item, details in cafeteria.menu.items():
            #price is discounted for staff and students
            discounted_price = details['price'] * (1 - (self.discount / 100))
            detailed_menu[item] = (details['description'], discounted_price, details['quantity'])
        return detailed_menu
    
    #this method is only available for staff and students
    def add_balance(self, amount):
        """Adds balance to the account.

        Args:
            amount (int): the amount to be added to the balance
            
        Returns:
            str: A message indicating the success of the balance addition
        """
        assert amount>0, "Amount should be greater than 0"
        self.balance+=amount
        return f"{amount}dkk added to the balance of {self.name}. The new balance is {self.balance}dkk"
        
    #this method is only available for staff and students 
    def place_order(self, cafeteria_name, item, quantity):
        """Places an order in a cafeteria.

        Args:
            cafeteria_name (String): the cafeteria where the order is to be placed
            item (string): the item to be ordered
            quantity (int): number of items to be ordered
            
        Returns:
            tuple: A tuple containing a potential message and the order object
        """
        cafeteria=self.university.get_cafeteria(cafeteria_name)
        assert cafeteria!=None, f"Sorry, {cafeteria_name} is not available in the university"
        assert quantity>0, "Quantity should be greater than 0"
        if item in cafeteria.menu:
            #calculating the price after discount for full order           
            price = cafeteria.menu[item]['price']*quantity*(1-(self.discount/100))
            if self.balance < price:
                raise ValueError(f"Sorry, you do not have enough balance to place this order")
            
            #placing the order with the cafeteria
            order=cafeteria.process_order(self.customer_id, self.customer_type, item, quantity, self.discount)
            
            #updating the balance based on the actual order (may be lower quantity)
            self.balance-=order[1].price
            self.orders.append(order[1])
            return order
                
        else:
            raise ValueError(f"Sorry, {item} is not available in the menu")
        
    
    def view_orders(self):
        """Lets the customer view all the orders placed by them and not picked up yet."""
        return self.orders
    
    def get_balance(self):
        """Returns the balance of the customer."""
        return self.balance
    
    def pick_up_order(self, order_id):
        """Lets the customer pick up an order from a cafeteria.

        Args:
            order_id (int): the id of the order to be picked up
        
        Returns: 
            the success or failure message of the order pick up
        """
        for order in self.orders:
            if order.order_id == order_id:
                self.orders.remove(order)
                return order.pick_up()
        raise ValueError(f"Sorry, order with id {order_id} not found")
    
    def search_menus(self, item):
        """Lets the customer search for an item in all the cafeterias of the university.

        Args:
            item (String): the item to be searched

        Returns:
           list: A list containing the details of all items with the given name in the university.
        """
        result=self.university.search_menu(item)
        if result[0]!=False:
            for i in range(len(result)):
                result[i][2]=result[i][2]*(1-(self.discount/100))
            return result
        else:
            return result
        

# %% [markdown]
# #### Student
# The first subclass of customer

# %%
class Student(General_Customer):
    def __init__(self, name, student_id, university):
        super().__init__(name, student_id, university, "Student", 20)

# %% [markdown]
# #### Staff
# 
# Staff has a different discount.

# %%
class Staff(General_Customer):
    def __init__(self, name, staff_id, university):
        super().__init__(name, staff_id, university, "Staff", 10)

# %% [markdown]
# #### Guest
# Guests cannot order online and have no account. They can merely view the menu. Therefore, other functions give Permission Errors.

# %%
class Guest(General_Customer):
    def __init__(self, name, university):
        super().__init__(name, None, university, "Guest", 0)
    
    def place_order(self, cafeteria, item, quantity):
        raise PermissionError("Guests cannot place orders online. Please book in person.")
    
    def add_balance(self, amount):
        raise PermissionError("Guests do not have a balance to add to.")
    
    def get_balance(self):
        raise PermissionError("Guests do not have a balance.")
    
    def view_orders(self):
        raise PermissionError("Guests do not have any orders.")
    
    def pick_up_order(self, order_id):
        raise PermissionError("Guests cannot pick up orders.")
    
        
    

# %% [markdown]
# #### Cafeteria
# 
# The cafeteria can add and edit the menu with multiple methods, both full uploads and individual additions and changes. They can process, complete and cancel orders and review the most popular items in order. Closing the cafeteria is also possible to reset the cafeteria at the end of a day. For popular items, we use merge sort

# %%

import copy

class Cafeteria:
    def __init__(self, name, university):
        self.name = name
        self.university = university
        self.menu = {}
        self.orders = []
        self.item_popularity = {}
        self.revenue=0
        
    def add_item(self, item, description, price, quantity):
        """Adds an item to the menu of the cafeteria.

        Args:
            item (string): the name of the item
            description (string): the description of the item
            price (int): the price of the item
            quantity (int): the quantity of the item available
        
        Returns:
            str: A message indicating the success of the item addition
        """
        assert price>0, "Price should be greater than 0"
        assert quantity>0, "Quantity should be greater than 0"
        self.menu[item] = {'description': description, 'price': price, 'quantity': quantity, 'cafeteria': self.name}
        # adding an item can be solved in-place, so no need to update the sorted menu
        self.university.update_sorted_menu(item, quantity, self.name, description, price)
        return f"{item} added to the menu"
        
    
    def upload_menu(self, new_menu):
        """Uploads the menu to the cafeteria.

        Args:
            menu (dict): a dictionary containing the items and their details
            
        Returns:
            str: A message indicating the success of the menu upload
        """
        assert type(new_menu)==dict, "Menu should be a dictionary"
        #deepcopy is used to avoid any changes in the original menu, especially when adding the attribute 'cafeteria'
        self.menu = copy.deepcopy(new_menu)
        for key in self.menu.keys():
            self.menu[key]['cafeteria'] = self.name
        # uploading a menu can change the order of the items, so the sorted menu should be updated    
        self.university.is_sorted = False
        return "Menu uploaded successfully"
        
    def update_item(self, item_name, description, price, quantity, new_item_name=None):
        """Updates the description, price, and quantity of an item in the menu. Optionally updates the name.
        Args:
            item_name (string): the current name of the item
            description (string): the new description of the item
            price (int): the new price of the item
            quantity (int): the new quantity of the item
            new_item_name (string, optional): the new name of the item
        
        Returns:
            str: A message indicating the success of the item update
        """
        assert price > 0, "Price should be greater than 0"
        assert quantity > 0, "Quantity should be greater than 0"
        if item_name in self.menu:
            if new_item_name:
                self.menu[new_item_name] = self.menu.pop(item_name)
                message=f"{item_name} updated to {new_item_name} with description: {description}, price: {price}dkk and quantity: {quantity}"
                item_name = new_item_name
                # updating the name can is a large change, so the sorted menu has to be fully re-sorted
                self.university.is_sorted = False
                
            else:
                #changing the description, price, and quantity can be solved in-place, so no need to update the sorted menu fully
                self.university.update_sorted_menu(item_name, quantity, self.name, description, price)
                message=f"{item_name} updated with description: {description}, price: {price}dkk and quantity: {quantity}"
            self.menu[item_name]['description'] = description
            self.menu[item_name]['price'] = price
            self.menu[item_name]['quantity'] = quantity
            return message
        else:
            raise ValueError(f"Sorry, {item_name} is not available in the menu")
        
    def restock_item(self, item, quantity):
        """Restocks an item in the menu.

        Args:
            item (string): the name of the item
            quantity (int): the quantity to be added to the stock
        
        Returns:
            str: A message indicating the success of the restocking
        """
        assert quantity>0, "Quantity should be greater than 0"
        if item in self.menu:
            self.menu[item]['quantity']+=quantity
            self.university.update_sorted_menu(item, self.menu[item]['quantity'], self.name, self.menu[item]['description'], self.menu[item]['price'])
            return f"{quantity} {item}(s) added to the stock. The new quantity is {self.menu[item]['quantity']}"
        else:
            raise ValueError(f"Sorry, {item} is not available in the menu")
        
    def remove_item(self, item):
        """Removes an item from the menu.

        Args:
            item (string): the name of the item
        
        Returns:
            str: A message indicating the success of the item removal
        """
        if item in self.menu:
            self.menu.pop(item)
            self.university.remove_item_from_sorted_menu(item, self.name)
            return f"{item} removed from the menu"
        else:
            raise ValueError(f"Sorry, {item} is not available in the menu")
    
    def process_order(self, customer_id, customer_type, item, quantity, discount=0):
        """Processes an order placed by a customer.

        Args:
            customer_id (int): the id of the customer placing the order
            customer_type (string): the type of the customer placing the order
            item (string): the item to be ordered
            quantity (int): number of items to be ordered
            discount (int): the discount to be applied to the order

        Returns:
            tuple: A tuple containing a potential message and the order object
        """
        assert quantity>0, "Quantity should be greater than 0"
        assert discount>=0, "Discount should be greater than or equal to 0"
        assert discount<=100, "Discount should be less than or equal to 100"
        assert self.university.get_customer(customer_id)!=None, f"Sorry, customer with id {customer_id} not found"
        if item in self.menu:
            message= None
            if self.menu[item]['quantity'] < quantity and self.menu[item]['quantity'] > 0:
                quantity = self.menu[item]['quantity']
                message= f"Sorry, only {self.menu[item]['quantity']} {item}(s) available"
            elif self.menu[item]['quantity'] == 0:
                raise ValueError(f"Sorry, {item} is out of stock")
            order = Order(self, customer_id, customer_type, item, quantity, self.menu[item]['price'], discount)
            if item not in self.item_popularity:
                self.item_popularity[item] = 0
            self.item_popularity[item] += quantity
            self.menu[item]['quantity']-=quantity
            self.orders.append(order)
            return (message, order)
        else:
            raise ValueError(f"Sorry, {item} is not available in the menu")
        
    def view_orders(self):
        """Lets the cafeteria view all the orders placed by customers and not picked up yet."""
        return self.orders
            
    
    def complete_order(self, order_id):
        """Completes an order placed by a customer.

        Args:
            order (int): the order object to be completed
        """
        for order in self.orders:
            if order.order_id == order_id:
                self.orders.remove(order)
                self.university.update_sorted_menu(order.item, order.quantity, self.name)
                self.revenue+=order.price
                return order.complete()
        raise ValueError(f"Order {order_id} not found")
        
    
    def cancel_order(self, order_id):
        """Cancels an order placed by a customer.

        Args:
            order (int): the order object to be cancelled
        """
        for order in self.orders:
            if order.order_id == order_id:
                self.orders.remove(order)
                if order.item in self.menu:
                    self.menu[order.item]['quantity']+=order.quantity
                else:
                    self.menu[order.item] = {'description': None, 'price': order.price/(order.quantity*(1-(order.discount/100))), 'quantity': order.quantity, 'cafeteria': self.name}
                return order.cancel()
        raise ValueError(f"Order {order_id} not found")
    
    def close_cafeteria(self):
        """Closes the cafeteria for the day and returns the revenue generated. The open orders are cancelled and the menu and popularity is cleared.
        
        Returns:
            int: The revenue generated by the cafeteria
        """
        return_value=self.revenue
        for order in self.orders:
            self.cancel_order(order.order_id)
        self.item_popularity = {}
        self.menu = {}
        self.university.is_sorted = False
        self.revenue = 0
        return return_value
    
    def popular_items(self, n):
        """Returns the n most popular items in the cafeteria.

        Args:
            n (int): the number of items to be printed
        
        Returns:
           list: A list of tuples containing the item name and its popularity
        """
        assert n>0, "n should be greater than 0"
        def merge_sort(items):
            if len(items) <= 1:
                return items

            # Split into two halves
            mid = len(items) // 2
            left_half = merge_sort(items[:mid])
            right_half = merge_sort(items[mid:])

            # Merge sorted halves
            return merge(left_half, right_half)

        def merge(left, right):
            sorted_items = []
            while len(left)>0 and len(right)>0:
                # Compare the second element (popularity)
                if left[0][1] >= right[0][1]:
                    sorted_items.append(left.pop(0))
                else:
                    sorted_items.append(right.pop(0))

            # Append any remaining items
            if len(left) > 0:
                sorted_items.extend(left)
            elif len(right) > 0:
                sorted_items.extend(right)
            return sorted_items
                
        
        # Convert dictionary to a list of tuples (item, popularity)
        items = list(self.item_popularity.items())
        # Sort using merge sort
        sorted_items = merge_sort(items)
        # Return the top N items
        return sorted_items[:n]

# %% [markdown]
# #### Order
# 
# Order simply manages the orders themselves.

# %%

class Order:
    class_counter=1
    def __init__(self, cafeteria, customer_id, customer_type, item, quantity, price, discount=0):
        self.order_id = Order.class_counter
        self.cafeteria = cafeteria
        self.customer_id = customer_id
        self.customer_type = customer_type
        self.item = item
        self.quantity = quantity
        self.price = price*quantity*(1-(discount/100))
        self.discount = discount
        #for simplicity, we assume all orders are accepted as the check is done before creating the order
        self.status = "Accepted"
        Order.class_counter+=1
        
    def __str__(self):
        return f"({self.status}) Order {self.order_id} by {self.customer_type} {self.customer_id} for {self.quantity} {self.item}(s) for {self.price}dkk"	
    
    def __repr__(self):
        return self.__str__()
    
    def total_price(self):
        return self.price
    
    def complete(self):
        self.status = "Completed"
        return f"Order {self.order_id} completed"
    
    def cancel(self):
        self.status = "Cancelled"
        #Refund
        for customer in self.cafeteria.university.all_customers():
            if customer.customer_id == self.customer_id:
                customer.balance+=self.price
        return f"Order {self.order_id} cancelled"
        
        
    def pick_up(self):
        self.status = "Picked Up"
        return f"Order {self.order_id} picked up"
        
    

# %% [markdown]
# #### University
# 
# University is the central administration of all cafeterias. It adds students, staff, cafeterias and manages them. It keeps a sorted menu of all menu items across all cafeterias for easy access and searching. It also simulates customers and days and has a central closing function for all cafeterias. For the sorted menu, we use in-place updating and insertion sort.

# %%
import random
random.seed(0)

class University:
    def __init__(self, name):
        self.name = name
        self.cafeterias = []
        self.students = []
        self.staff = []
        self.sorted_menu = []
        self.is_sorted = False
        
    def add_student(self, name, student_id):
        assert student_id not in [student.customer_id for student in self.students], f"Student with id {student_id} already exists"
        student = Student(name, student_id, self)
        self.students.append(student)
        return student
    
    def add_staff(self, name, staff_id):
        assert staff_id not in [staff.customer_id for staff in self.staff], f"Staff with id {staff_id} already exists"
        staff = Staff(name, staff_id, self)
        self.staff.append(staff)
        return staff
    
    def all_customers(self):
        """Returns all the customers in the university.

        Returns:
            list: A list containing all the customers in the university
        """
        return self.students + self.staff
    
    def get_customer(self, customer_id):
        """"
        Returns the customer with the given id."""
        for customer in self.all_customers():
            if customer.customer_id == customer_id:
                return customer
        return None
    
    def add_cafeteria(self, name):
        assert name not in [cafeteria.name for cafeteria in self.cafeterias], f"Cafeteria with name {name} already exists"
        cafeteria = Cafeteria(name, self)
        self.cafeterias.append(cafeteria)
        return cafeteria
    
    def get_cafeteria(self, name):
        """" Returns the cafeteria with the given name.""" 
        for cafeteria in self.cafeterias:
            if cafeteria.name == name:
                return cafeteria
        return None
    
    def generate_customers(self, n_students, n_staff):
        for i in range(n_students):
            self.add_student(f"Student {i+1}", i*1000+random.randint(1, 999))
        for i in range(n_staff):
            self.add_staff(f"Staff {i+1}", i*1000+random.randint(1, 999))
    
    def update_sorted_menu(self, item, quantity, cafeteria_name, description=None, price=None):
        """Updates the sorted menu of the university in-place for minor changes and higher efficiency.

        Args:
            item (string): the name of the item
            quantity (int): the quantity of the item available
            cafeteria_name (string): the name of the cafeteria
            description (string): the description of the item
            price (int): the price of the item
        """
        assert quantity>0, "Quantity should be greater than 0"
        assert cafeteria_name in [cafeteria.name for cafeteria in self.cafeterias], f"Sorry, {cafeteria_name} is not available in the university"
        #only update if the menu is sorted
        if self.is_sorted:
            for i in range(len(self.sorted_menu)):
                if self.sorted_menu[i][0] == item:
                    # Remove the item from the list
                    prev_item = self.sorted_menu.pop(i)

                    # Re-insert the item at the correct position
                    j = len(self.sorted_menu) - 1
                    while j >= 0 and self.sorted_menu[j][0] > item[0]:
                        j -= 1
                    if description == None:
                        self.sorted_menu.insert(j + 1, (item, prev_item[1], prev_item[2], quantity, cafeteria_name))
                    else:
                        self.sorted_menu.insert(j + 1, (item,  description, price, quantity, cafeteria_name))
                    break
    
    def remove_item_from_sorted_menu(self, item, cafeteria_name):
        """Removes an item from the sorted menu of the university.

        Args:
            item (string): the name of the item
            cafeteria_name (string): the name of the cafeteria
        """
        if self.is_sorted:
            for i in range(len(self.sorted_menu)):
                if self.sorted_menu[i][0] == item and self.sorted_menu[i][4] == cafeteria_name:
                    self.sorted_menu.pop(i)
                    break
      
    def view_sorted_menu(self):
        """Returns the sorted menu of the university as a list of dictionaries.
        
        Returns:
            list: list of dictionaries containing the item, description, price, quantity, and cafeteria of each item in the menu
        """
        if not self.is_sorted:
            self.sort_menu()
        menu_list = []
        for item in self.sorted_menu:
            menu_item = {
            "item": item[0],
            "description": item[1],
            "price": item[2],
            "quantity": item[3],
            "cafeteria": item[4]
            }
            menu_list.append(menu_item)
        return menu_list
    
    def sort_menu(self):
        """
        Generates a sorted complete menu using insertion sort and updates the cache.
        
        Returns:
            The sorted complete menu.
        """
        complete_menu = []        
        i=0
        # Sort using insertion sort
        for cafeteria in self.cafeterias:
   
            for name in cafeteria.menu.keys():
                item=(name, cafeteria.menu[name]['description'], cafeteria.menu[name]['price'],cafeteria.menu[name]['quantity'],cafeteria.menu[name]['cafeteria'])
                complete_menu.append(item)
                j=i-1
                while j >= 0 and (complete_menu[j][0] > name or (complete_menu[j][0] == name and complete_menu[j][4]>item[4])):  # Sort by item name
                    complete_menu[j + 1] = complete_menu[j]
                    j -= 1
                complete_menu[j + 1] = item
                i+=1

        # Update the cache
        self.sorted_menu = complete_menu
        self.is_sorted = True
        return self.sorted_menu
    
    def search_menu(self, item_name):
        """Searches for an item in the menu of the university.

        Args:
            item_name (String): the name of the item to be searched

        Returns:
            list: a list of tuples containing the item details
        """
        # Sort the menu if it is not up-to-date
        if not self.is_sorted:
            self.sort_menu()

        # Perform binary search
        low, high = 0, len(self.sorted_menu) - 1
        results = []

        while low <= high:
            mid = (low + high) // 2
            mid_item = self.sorted_menu[mid][0]

            if mid_item == item_name:
                # Find all matches
                results.append([self.sorted_menu[mid][4], self.sorted_menu[mid][1], self.sorted_menu[mid][2], self.sorted_menu[mid][3]])

                # Check neighbors for duplicates
                left, right = mid - 1, mid + 1
                while left >= 0 and self.sorted_menu[left][0] == item_name:
                    results.append([self.sorted_menu[left][4], self.sorted_menu[left][1], self.sorted_menu[left][2], self.sorted_menu[left][3]])
                    left -= 1
                while right < len(self.sorted_menu) and self.sorted_menu[right][0] == item_name:
                    results.append([self.sorted_menu[right][4], self.sorted_menu[right][1], self.sorted_menu[right][2], self.sorted_menu[right][3]])
                    right += 1
                return results

            elif mid_item < item_name:
                low = mid + 1
            else:
                high = mid - 1

        return False, f"Item '{item_name}' not found in any cafeteria."
    
    
    def simulate_day(self, n=10):
        """Simulates a day in the university.
        
        Args:
            n (int): maximum number of orders to be placed in each cafeteria, at least 5
            
            
        Returns:
            tuple: A tuple containing the number of cancelled orders, completed orders, successful orders, failed orders, and a log of all the events
            """
        assert n>=5, "n should be at least 5"
        cancelled_orders = 0
        completed_orders = 0
        successful_orders = 0
        failed_orders = 0
        log = []
        
        for cafeteria in self.cafeterias:
            for i in range(random.randint(5, n)):
                if i % 5 == 4:
                    popular_items = cafeteria.popular_items(5)
                    for item in popular_items:
                        cafeteria.restock_item(item[0], random.randint(10, 50))
                        log.append(f"Restocked {item[0]} in {cafeteria.name}")
                
                customer = random.choice(self.all_customers())
                customer.add_balance(random.randint(10, 500))
                log.append(f"Added balance to {customer.name}")
                item = random.choice(list(cafeteria.menu.keys()))
                quantity = random.randint(1, 5)
                
                try:
                    order = customer.place_order(cafeteria.name, item, quantity)
                    log.append(f"{customer.name} placed order for {quantity} {item}(s) from {cafeteria.name}")
                    if random.random() < 0.1:
                        cafeteria.cancel_order(order[1].order_id)
                        cancelled_orders += 1
                        log.append(f"Order for {quantity} {item}(s) from {cafeteria.name} was cancelled")
                    elif random.random() > 0.1:
                        cafeteria.complete_order(order[1].order_id)
                        completed_orders += 1
                        log.append(f"Order for {quantity} {item}(s) from {cafeteria.name} was completed")
                        if random.random() > 0.2:
                            customer.pick_up_order(order[1].order_id)
                            successful_orders += 1
                            log.append(f"Order for {quantity} {item}(s) from {cafeteria.name} was picked up")
                except ValueError as e:
                    failed_orders += 1
                    log.append(f"Order for {quantity} {item}(s) from {cafeteria.name} failed: {str(e)}")
                   
        return cancelled_orders, completed_orders, successful_orders, failed_orders, log
    
    def close_university(self):
        """Closes the university for the day.
        
        Returns:
            tuple: A tuple containing the total revenue and the revenue by cafeteria as a dictionary
        """
        total_revenue = 0
        revenue_by_cafeteria = {}  
        for cafeteria in self.cafeterias:
            total_revenue += cafeteria.revenue
            
            revenue_by_cafeteria[cafeteria.name] = cafeteria.close_cafeteria()
        return total_revenue, revenue_by_cafeteria
        



# %% [markdown]
# #### Test
# 
# Testing Playground.

# %%
def setup_example():
   #creating a university
   university = University("CBS")

   #adding a cafeteria to the university
   university.add_cafeteria("Solbjerg Plads")
   university.add_cafeteria("Dalgas Have")
   university.add_cafeteria("Kilen")
   university.add_cafeteria("Porcelænshaven")
   university.generate_customers(1000,100)
   return university

def upload_example_menus(university):
   #adding items to the menu of the cafeterias
   daily_menu = { "Coffee": {"description": "A standard filter.", "price": 25, "quantity": 10},
            "Tea": {"description": "A cup of green or black tea", "price": 20, "quantity": 15},
            "Sandwich": {"description": "A chicken or tomato morzarella sandwich", "price": 35, "quantity": 5},
            "Kannelbullar": {"description": "A Danish cinnamon bun", "price": 15, "quantity": 20},
            "Croissant": {"description": "A buttery croissant", "price": 20, "quantity": 10},
               "Salad": {"description": "A fresh salad with vegetables", "price": 40, "quantity": 5}}

   lunch_menu = { "Pasta": {"description": "Pasta with tomato sauce", "price": 45, "quantity": 10},
               "Pizza": {"description": "A slice of pizza", "price": 30, "quantity": 15},
               "Burger": {"description": "A beef or veggie burger", "price": 50, "quantity": 5},
               "Sushi": {"description": "A sushi roll", "price": 35, "quantity": 20},
               "Soup": {"description": "A bowl of soup", "price": 25, "quantity": 10}}

   reduced_menu = { "Pasta": {"description": "Pasta with tomato sauce", "price": 45, "quantity": 10},
               "Pizza": {"description": "A slice of pizza", "price": 30, "quantity": 5},
               "Burger": {"description": "A beef or veggie burger", "price": 50, "quantity": 5}}

   drink_menu = { "Coca Cola": {"description": "A can of Coca Cola", "price": 15, "quantity": 10},
               "Fanta": {"description": "A can of Fanta", "price": 15, "quantity": 10},
               "Faxe Kondi": {"description": "A can of Faxe Kondi", "price": 15, "quantity": 10},
               "Water": {"description": "A bottle of water", "price": 10, "quantity": 10}}

   snack_menu = { "Chips": {"description": "A bag of chips", "price": 10, "quantity": 10},
               "Chocolate": {"description": "A chocolate bar", "price": 10, "quantity": 10},
               "Gum": {"description": "A pack of gum", "price": 5, "quantity": 10},
               "Popcorn": {"description": "A bag of popcorn", "price": 15, "quantity": 10}}
   university.cafeterias[0].upload_menu(daily_menu|snack_menu|lunch_menu)
   university.cafeterias[1].upload_menu(daily_menu|lunch_menu)
   university.cafeterias[2].upload_menu(daily_menu|reduced_menu)
   university.cafeterias[3].upload_menu(daily_menu|drink_menu)





# %% [markdown]
# #### Visual Interface
# 
# This goes beyond the scope but creates a fun environment. Feel free to check it out using student 865!

# %%
from tkinter import *

class GUI:
    def __init__(self, university):
        self.university = university
        self.window = Tk()
        self.window.title("University Cafeteria System")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        self.reset()
        
    def reset(self):
        self.current_cafeteria = None
        self.current_item = None
        self.current_quantity = None
        self.current_order = None
        self.current_order_id = None
        self.current_search = None
        self.current_search_results = None
        self.current_search_index = 0
        self.current_popular_items = None
        self.current_popular_index = 0
        self.current_balance = None
        self.current_balance_label = None
        self.current_balance_entry = None
        self.current_balance_button = None
        self.current_pickup = None
        self.current_pickup_label = None
        self.current_pickup_entry = None
        self.current_pickup_button = None
        self.current_order_label = None
        self.current_order_entry = None
        self.current_order_button = None
        self.current_search_label = None
        self.current_search_entry = None
        self.current_search_button = None
        self.current_search_results_details = None
        self.current_search_results_label = None
        self.current_search_results_entry = None
        self.current_search_results_button = None
        self.current_popular_items_label = None
        self.current_popular_items_entry = None
        self.current_popular_items_button = None
        self.current_popular_index_label = None
        self.current_popular_index_entry = None
        self.current_popular_index_button = None
        self.current_menu = None
        self.current_menu_label = None
        self.current_menu_button = None
        self.current_menu_index = 0
        self.current_menu_index_label = None
        self.current_menu_index_entry = None
        self.current_menu_index_button = None
        self.current_order_id_label = None
        self.current_order_id_entry = None
        self.current_order_id_button = None
        self.current_order_id = None
        self.current_order_status = None
        self.current_order_status_label = None
        self.current_order_status_button = None
        self.current_order_status_entry = None
        self.current_order_status_index = 0
        self.current_order_status_index_label = None
        self.current_order_status_index_entry = None
        self.university_closed = False
        self.start()
        
    def start(self):
        self.set_mode()
        self.window.mainloop()
        
    def set_mode(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Select Mode", font=("Arial", 20)).pack()
        Button(self.window, text="Customer View", command=self.create_login).pack()
        Button(self.window, text="Cafeteria View", command=self.cafeteria_view_backend).pack()
        Button(self.window, text="University View", command=self.university_view).pack()
        Button(self.window, text="Exit", command=self.end).pack()
        
        
        
    def end(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.window.destroy()
        self.window.quit()
        
        
    # Customer View
    
    def create_login(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Welcome to the University Cafeteria System of {self.university.name}", font=("Arial", 20)).pack()
        Label(self.window, text="Please select your customer type and enter your ID").pack()
        self.customer_type = StringVar()
        self.customer_type.set("Student")
        Radiobutton(self.window, text="Student", variable=self.customer_type, value="Student").pack()
        Radiobutton(self.window, text="Staff", variable=self.customer_type, value="Staff").pack()
        Radiobutton(self.window, text="Guest", variable=self.customer_type, value="Guest").pack()
        self.customer_id = Entry(self.window)
        self.customer_id.pack()
        Button(self.window, text="Login", command=self.login).pack()
        Button(self.window, text="Back", command=self.set_mode).pack()
    
    def login(self):
        customer_type = self.customer_type.get()
        customer_id = self.customer_id.get()
        customer = None
        if customer_type == "Student":
            customer = self.university.get_customer(int(customer_id))
        elif customer_type == "Staff":
            customer = self.university.get_customer(int(customer_id))
        elif customer_type == "Guest":
            customer = Guest("Guest", self.university)
        if customer == None:
            Label(self.window, text="Invalid ID. Please try again.").pack()
        else:
            self.current_customer = customer
            self.create_main_menu()
    
    def create_main_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()

        Label(self.window, text=f"Welcome, {self.current_customer}").pack()
        
        if self.current_customer.customer_type != "Guest":
            Button(self.window, text="View Cafeterias & Order", command=self.view_cafeterias).pack()
            Button(self.window, text="View Orders & Pick-Up", command=self.view_orders).pack()
            Button(self.window, text="Add Balance", command=self.add_balance).pack()
        else:
            Button(self.window, text="View Cafeterias", command=self.view_cafeterias).pack()
            
        Button(self.window, text="Search Menu", command=self.search_menu).pack()
        Button(self.window, text="Logout", command=self.set_mode).pack()
     
    def view_cafeterias(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Select Cafeteria", font=("Arial", 20)).pack()
        for cafeteria in self.university.cafeterias:
            Button(self.window, text=cafeteria.name, command=lambda cafeteria=cafeteria: self.cafeteria_view_customer(cafeteria)).pack()
        Button(self.window, text="Back", command=self.create_main_menu).pack()
    
    def cafeteria_view_customer(self, cafeteria):
        self.current_cafeteria = cafeteria
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Cafeteria: {self.current_cafeteria.name}", font=("Arial", 20)).pack()
        

        if self.current_customer.customer_type != "Guest":
            Button(self.window, text="View Menu & Order", command=self.view_menu).pack()
            Button(self.window, text="Place Order Manually", command=self.place_order_manually).pack()
        else:
            Button(self.window, text="View Menu", command=self.view_menu).pack()
        Button(self.window, text="Back", command=self.view_cafeterias).pack()
        
    def view_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Menu", font=("Arial", 20)).pack()
        menu = self.current_customer.view_menu(self.current_cafeteria.name)
        for item, details in menu.items():
            price, quantity = details
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=f"{item} - Price: {price} DKK (Quantity: {quantity})").pack(side=LEFT)
            if self.current_customer.customer_type != "Guest":
                Button(frame, text="Order", command=lambda item=item: self.place_order(self.current_cafeteria, item)).pack(side=RIGHT)
                
        Button(self.window, text="View Detailed Menu", command=self.view_detailed_menu).pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_view_customer(self.current_cafeteria)).pack()
    
    def view_detailed_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Detailed Menu", font=("Arial", 20)).pack()
        menu = self.current_customer.view_detailed_menu(self.current_cafeteria.name)
        for item, details in menu.items():
            description, price, quantity = details
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=f"{item} - {description} - Price: {price} DKK (Quantity: {quantity})").pack(side=LEFT)
            if self.current_customer.customer_type != "Guest":
                Button(frame, text="Order", command=lambda item=item: self.place_order(self.current_cafeteria, item)).pack(side=RIGHT)
        Button(self.window, text="View Compact Menu", command=self.view_menu).pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_view_customer(self.current_cafeteria)).pack()
    
    def place_order_manually(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Place Order", font=("Arial", 20)).pack()
        Label(self.window, text=f"Current Balance: {self.current_customer.balance} DKK").pack()
        Button(self.window, text="Add Balance", command=self.add_balance).pack()
        Label(self.window, text="Item").pack()
        self.current_item = Entry(self.window)
        self.current_item.pack()
        Label(self.window, text="Quantity").pack()
        self.current_quantity = Entry(self.window)
        self.current_quantity.pack()
        Button(self.window, text="Order", command=self.place_order_action).pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_view_customer(self.current_cafeteria)).pack()
        
    def place_order(self, cafeteria, item):
        self.current_cafeteria = cafeteria
        self.current_item_name = item
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Place Order for {item} at {cafeteria.name}", font=("Arial", 20)).pack()
        Label(self.window, text=f"Current Balance: {self.current_customer.balance} DKK").pack()
        Button(self.window, text="Add Balance", command=self.add_balance).pack()
        Label(self.window, text=f"Available Quantity: {self.current_cafeteria.menu[item]['quantity']}").pack()
        Label(self.window, text="Quantity").pack()
        self.current_quantity = Entry(self.window)
        self.current_quantity.pack()
        Button(self.window, text="Order", command=self.place_order_action).pack()
        Button(self.window, text="Back", command=lambda: self.view_cafeterias()).pack()

    def place_order_action(self):
        if not hasattr(self, 'current_item_name'):
            item = self.current_item.get()
        else:
            item = self.current_item_name
        
        try:
            quantity = int(self.current_quantity.get())
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
            return

        try:
            message, order = self.current_customer.place_order(self.current_cafeteria.name, item, quantity)
            if message != None:
                Label(self.window, text=message).pack()
            if order:
                self.current_order = order
                self.create_order_menu(message)
        except KeyError:
            Label(self.window, text="Item not found. Please check the spelling and try again.").pack()
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
    
            
    def create_order_menu(self, message):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Order Menu", font=("Arial", 20)).pack()
        if message != None:
            Label(self.window, text=message).pack()
        Label(self.window, text=self.current_order).pack()
        Button(self.window, text="Back", command=self.create_main_menu).pack()
    
        
    def view_orders(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Orders", font=("Arial", 20)).pack()
        orders = self.current_customer.view_orders()
        for order in orders:
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=order).pack(side=LEFT)
            if order.status == "Completed":
                Button(frame, text="Pick-Up", command=lambda order=order: self.pick_up_order(order)).pack(side=RIGHT)
        Button(self.window, text="Back", command=self.create_main_menu).pack()

    def pick_up_order(self, order):
        message = self.current_customer.pick_up_order(order.order_id)
        self.view_orders_with_message(message)
        
    def view_orders_with_message(self, message):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Orders", font=("Arial", 20)).pack()
        orders = self.current_customer.view_orders()
        for order in orders:
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=order).pack(side=LEFT)
            if order.status == "Completed":
                Button(frame, text="Pick-Up", command=lambda order=order: self.pick_up_order(order)).pack(side=RIGHT)
        Button(self.window, text="Back", command=self.create_main_menu).pack()
        Label(self.window, text=message).pack()
    
    def add_balance(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Add Balance", font=("Arial", 20)).pack()
        Label(self.window, text=f"Current Balance: {self.current_customer.balance}").pack()
        self.current_balance = Entry(self.window)
        self.current_balance.pack()
        Button(self.window, text="Add", command=self.add_balance_action).pack()
        Button(self.window, text="Back", command=self.create_main_menu).pack()
    
    def add_balance_action(self):
        amount = int(self.current_balance.get())
        message = self.current_customer.add_balance(amount)
        Label(self.window, text=message).pack()
    
    def search_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Search Menu", font=("Arial", 20)).pack()
        self.current_search = Entry(self.window)
        self.current_search.pack()
        Button(self.window, text="Search", command=self.search_menu_action).pack()
        Button(self.window, text="Back", command=self.create_main_menu).pack()
    
    def search_menu_action(self):
        item_name = self.current_search.get()
        results = self.current_customer.search_menus(item_name)
        if results[0]==False:
            Label(self.window, text=results[1]).pack()
            return
        formatted_results = []
        for result in results:
            cafeteria, item, price, quantity = result
            formatted_results.append(f"Cafeteria: {cafeteria}, Description: {item}, Price: {price} DKK, Quantity: {quantity}")
        self.current_search_results = formatted_results
        self.current_search_results_details = results
        self.current_search_index = 0
        self.create_search_results(item_name)
    
    def create_search_results(self, item_name):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Search Results for {item_name}", font=("Arial", 20)).pack()
        self.current_search_results_label = Label(self.window, text=self.current_search_results[self.current_search_index])
        self.current_search_results_label.pack()
        self.current_search_index_label = Label(self.window, text=f"{self.current_search_index+1}/{len(self.current_search_results)}")
        self.current_search_index_label.pack()
        if self.current_customer.customer_type != "Guest":
            Button(self.window, text="Order here", command=lambda: self.place_order(university.get_cafeteria(self.current_search_results_details[self.current_search_index][0]), item_name)).pack()
        self.current_search_results_button = Button(self.window, text="Next", command=self.next_search_result)
        self.current_search_results_button.pack()
        Button(self.window, text="Back to Menu", command=self.search_menu).pack()
    
    def next_search_result(self):
        self.current_search_index += 1
        if self.current_search_index == len(self.current_search_results):
            self.current_search_index = 0
        self.current_search_results_label.config(text=self.current_search_results[self.current_search_index])
        self.current_search_index_label.config(text=f"{self.current_search_index+1}/{len(self.current_search_results)}")
        
 

    
    
        
    #Cafeteria View
        
    def cafeteria_view_backend(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Select Cafeteria", font=("Arial", 20)).pack()
        for cafeteria in self.university.cafeterias:
            Button(self.window, text=cafeteria.name, command=lambda cafeteria=cafeteria: self.cafeteria_administration(cafeteria)).pack()
        Button(self.window, text="Back", command=self.set_mode).pack()        
        
    def cafeteria_administration(self, cafeteria):
        self.current_cafeteria = cafeteria
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Cafeteria: {self.current_cafeteria.name}", font=("Arial", 20)).pack()
        
        Button(self.window, text="View & Complete Orders", command=self.view_cafeteria_orders).pack()
        Button(self.window, text="View & Edit Menu", command=self.view_cafeteria_menu).pack()
        Button(self.window, text="View Popular Items", command=self.popular_items).pack()
        Button(self.window, text="View Revenue", command=self.view_revenue).pack()
        Button(self.window, text="Close Cafeteria", command=self.close_cafeteria).pack()
        Button(self.window, text="Back", command=self.set_mode).pack()
    
    def view_cafeteria_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Menu", font=("Arial", 20)).pack()
        menu = self.current_cafeteria.menu
        for item, details in menu.items():
            description, price, quantity = details['description'], details['price'], details['quantity']
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=f"{item} - {description} - Price: {price} DKK (Quantity: {quantity})").pack(side=LEFT)
            Button(frame, text="Remove", command=lambda item=item: self.remove_item(item)).pack(side=RIGHT)
            Button(frame, text="Restock", command=lambda item=item: self.restock_item(item)).pack(side=RIGHT)
            Button(frame, text="Update", command=lambda item=item: self.update_item(item)).pack(side=RIGHT)
        Button(self.window, text="Add Item", command=self.add_item).pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
    
    def restock_item(self, item):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Restock {item}", font=("Arial", 20)).pack()
        current_quantity = self.current_cafeteria.menu[item]['quantity']
        Label(self.window, text=f"Current Quantity: {current_quantity}").pack()
        Label(self.window, text="Quantity").pack()
        self.current_quantity = Entry(self.window)
        self.current_quantity.pack()
        Button(self.window, text="Restock", command=lambda: self.restock_item_action(item)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
    
    def restock_item_action(self, item):
        quantity = int(self.current_quantity.get())
        message = self.current_cafeteria.restock_item(item, quantity)
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=message, font=("Arial", 20)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
        
    def update_item(self, item):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Update {item}", font=("Arial", 20)).pack()
        Label(self.window, text="Description").pack()
        self.current_description = Entry(self.window)
        self.current_description.pack()
        Label(self.window, text="Price").pack()
        self.current_price = Entry(self.window)
        self.current_price.pack()
        Label(self.window, text="Quantity").pack()
        self.current_quantity = Entry(self.window)
        self.current_quantity.pack()
        Button(self.window, text="Update", command=lambda: self.update_item_action(item)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
        
        # Display existing data
        current_data = self.current_cafeteria.menu[item]
        Label(self.window, text=f"Current Description: {current_data['description']}").pack()
        Label(self.window, text=f"Current Price: {current_data['price']}").pack()
        Label(self.window, text=f"Current Quantity: {current_data['quantity']}").pack()
    
    def update_item_action(self, item):
        description = self.current_description.get()
        price = int(self.current_price.get())
        quantity = int(self.current_quantity.get())
        message = self.current_cafeteria.update_item(item, description, price, quantity)
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=message, font=("Arial", 20)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
        
    def remove_item(self, item):
        message = self.current_cafeteria.remove_item(item)
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=message, font=("Arial", 20)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
    
    def view_cafeteria_orders(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Orders", font=("Arial", 20)).pack()
        orders = self.current_cafeteria.view_orders()
        for order in orders:
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=order).pack(side=LEFT)
            if order.status == "Accepted":
                Button(frame, text="Complete", command=lambda order=order: self.complete_order(order)).pack(side=RIGHT)
                Button(frame, text="Cancel", command=lambda order=order: self.cancel_order(order)).pack(side=RIGHT)
            elif order.status == "Completed":
                Button(frame, text="Cancel", command=lambda order=order: self.cancel_order(order)).pack(side=RIGHT)
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
    
    def view_cafeteria_orders_with_status(self, message):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Orders", font=("Arial", 20)).pack()
        orders = self.current_cafeteria.view_orders()
        for order in orders:
            frame = Frame(self.window)
            frame.pack()
            Label(frame, text=order).pack(side=LEFT)
            if order.status == "Accepted":
                Button(frame, text="Complete", command=lambda order=order: self.complete_order(order)).pack(side=RIGHT)
                Button(frame, text="Cancel", command=lambda order=order: self.cancel_order(order)).pack(side=RIGHT)
            elif order.status == "Completed":
                Button(frame, text="Cancel", command=lambda order=order: self.cancel_order(order)).pack(side=RIGHT)
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
        Label(self.window, text=message).pack()
    
    def complete_order(self, order):
        message = self.current_cafeteria.complete_order(order.order_id)
        self.view_cafeteria_orders_with_status(message)
    
    def cancel_order(self, order):
        message = self.current_cafeteria.cancel_order(order.order_id)
        self.view_cafeteria_orders_with_status(message)
    
    def add_item(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Add Item", font=("Arial", 20)).pack()
        Label(self.window, text="Item").pack()
        self.current_item = Entry(self.window)
        self.current_item.pack()
        Label(self.window, text="Description").pack()
        self.current_description = Entry(self.window)
        self.current_description.pack()
        Label(self.window, text="Price").pack()
        self.current_price = Entry(self.window)
        self.current_price.pack()
        Label(self.window, text="Quantity").pack()
        self.current_quantity = Entry(self.window)
        self.current_quantity.pack()
        Button(self.window, text="Add", command=self.add_item_action).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
        
    def add_item_action(self):
        item = self.current_item.get()
        description = self.current_description.get()
        
        try:
            price = int(self.current_price.get())
            if price <= 0:
                raise ValueError("Price must be a positive number.")
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
            return
        
        try:
            quantity = int(self.current_quantity.get())
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
            return
        
        message = self.current_cafeteria.add_item(item, description, price, quantity)
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=message, font=("Arial", 20)).pack()
        Button(self.window, text="Back", command=self.view_cafeteria_menu).pack()
        
    
    def popular_items(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Popular Items", font=("Arial", 20)).pack()
        Label(self.window, text="Enter the number of popular items to display:").pack()
        self.popular_items_count = Entry(self.window)
        self.popular_items_count.pack()
        Button(self.window, text="Show", command=self.show_popular_items).pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()

    def show_popular_items(self):
        try:
            count = int(self.popular_items_count.get())
            if count <= 0:
                raise ValueError("Number must be a positive integer.")
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
            return

        self.current_popular_items = self.current_cafeteria.popular_items(count)
        self.current_popular_index = 0
        if not self.current_popular_items:
            Label(self.window, text="No popular items available.").pack()
        else:
            self.create_popular_items()
    
    def create_popular_items(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Popular Items", font=("Arial", 20)).pack()
        item, popularity = self.current_popular_items[self.current_popular_index]
        self.current_popular_items_label = Label(self.window, text=f"{item} - Popularity: {popularity}")
        self.current_popular_items_label.pack()
        self.current_popular_index_label = Label(self.window, text=f"{self.current_popular_index+1}/{len(self.current_popular_items)}")
        self.current_popular_index_label.pack()
        self.current_popular_items_button = Button(self.window, text="Next", command=self.next_popular_item)
        self.current_popular_items_button.pack()
        Button(self.window, text="Back to Menu", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
    
    def next_popular_item(self):
        self.current_popular_index += 1
        if self.current_popular_index == len(self.current_popular_items):
            self.current_popular_index = 0
        item, popularity = self.current_popular_items[self.current_popular_index]
        self.current_popular_items_label.config(text=f"{item} - Popularity: {popularity}")
        self.current_popular_index_label.config(text=f"{self.current_popular_index+1}/{len(self.current_popular_items)}")
        self.current_popular_items_button.config(text="Next")
    
    def view_revenue(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"Revenue of {self.current_cafeteria.name}", font=("Arial", 20)).pack()
        Label(self.window, text=f"Current Revenue: {self.current_cafeteria.revenue} DKK").pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
    
    def close_cafeteria(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        message = self.current_cafeteria.close_cafeteria()
        Label(self.window, text=f"Revenue: {message} dkk. Cafeteria {self.current_cafeteria.name} now closed and the menu is taken offline.").pack()
        Button(self.window, text="Back", command=lambda: self.cafeteria_administration(self.current_cafeteria)).pack()
    
    
    
    
    
    # University View
        
    def university_view(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text=f"University: {self.university.name}", font=("Arial", 20)).pack()
        Button(self.window, text="View Sorted Menu", command=self.view_sorted_menu).pack()
        if self.university_closed == False:
            Button(self.window, text="Simulate a Day", command=self.simulate).pack()
            Button(self.window, text="Close University", command=self.close_university).pack()
        else:
            Button(self.window, text="Reopen University", command=self.reopen_university).pack()
        Button(self.window, text="Back", command=self.set_mode).pack()
    
    def view_sorted_menu(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Sorted Menu", font=("Arial", 20)).pack()
        
        # Create a canvas and a scrollbar
        canvas = Canvas(self.window)
        scrollbar = Scrollbar(self.window, orient=VERTICAL, command=canvas.yview)
        scrollable_frame = Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar.pack(side=RIGHT, fill=Y)

        sorted_menu = self.university.view_sorted_menu()
        for item in sorted_menu:
            item_name = item['item']
            description = item['description']
            price = item['price']
            quantity = item['quantity']
            cafeteria = item['cafeteria']
            frame = Frame(scrollable_frame)
            frame.pack()
            Label(frame, text=f"{item_name} - {description} - Price: {price} DKK (Quantity: {quantity}) - Cafeteria: {cafeteria}").pack(side=LEFT)
        Button(self.window, text="Back", command=self.university_view).pack()
        
    def simulate(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Simulate a Day", font=("Arial", 20)).pack()
        Label(self.window, text="Enter the number of orders possible per cafeteria (must be greater than 5):").pack()
        self.orders_per_cafeteria = Entry(self.window)
        self.orders_per_cafeteria.pack()
        Button(self.window, text="Simulate", command=self.simulate_action).pack()
        Button(self.window, text="Back", command=self.university_view).pack()
    
    def simulate_action(self):
        try:
            orders = int(self.orders_per_cafeteria.get())
            if orders <= 5:
                raise ValueError("Number of orders must be greater than 5.")
        except ValueError as e:
            Label(self.window, text=str(e)).pack()
            return
        
        for widget in self.window.winfo_children():
            widget.destroy()
        Label(self.window, text="Simulating a day...", font=("Arial", 20)).pack()
        cancelled_orders, completed_orders, successful_orders, failed_orders, _ = self.university.simulate_day(orders)
        Label(self.window, text=f"Cancelled Orders: {cancelled_orders}").pack()
        Label(self.window, text=f"Completed Orders: {completed_orders}").pack()
        Label(self.window, text=f"Successful Orders: {successful_orders}").pack()
        Label(self.window, text=f"Failed Orders: {failed_orders}").pack()
        Button(self.window, text="Back", command=self.university_view).pack()
    
    def close_university(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        total_revenue, revenue_by_cafeteria = self.university.close_university()
        self.university_closed = True
        Label(self.window, text=f"Total Revenue: {total_revenue}dkk").pack()
        for cafeteria in revenue_by_cafeteria:
            Label(self.window, text=f"{cafeteria}: {revenue_by_cafeteria[cafeteria]}dkk").pack()
        Button(self.window, text="Back", command=self.set_mode).pack()
        
    def reopen_university(self):
        for widget in self.window.winfo_children():
            widget.destroy()
        self.university_closed = False
        upload_example_menus(self.university)
        Label(self.window, text="University is now open.").pack()
        Button(self.window, text="Back", command=self.university_view).pack()



 
# Test and use GUI
university=setup_example()
upload_example_menus(university)
testGUI = GUI(university)


