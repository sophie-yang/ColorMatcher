#!/usr/bin/python
import re
import glob
import json

class ElementList:
  labels = []
  icons = []
  cells = []
  controllers = []
  backgroundColors = []

  def totalElementCount(self):
    return len(self.controllers) + len(self.labels) + len(self.labels) + len(self.icons) + len(self.backgroundColors)


class ElementPattern:
  labelPattern = re.compile(r'(\S*)(\s*:\s*|\s*=\s*)(XOLabel|UILabel)')
  iconPattern = re.compile(r'(.*)(\s*=?\s*)(XOKitIcon.*)')
  cellPattern = re.compile(r'(class\s*)(\S*)(\s*:.*Cell)')
  controllerPattern = re.compile(r'(class\s*)(\S*)(\s*:\s*XOViewController|UITabBarController|TabbedContainerViewController|XOWebViewController|OnboardingStepViewController|RegistrationChildPageViewController|XOTableViewController|UINavigationViewController|UIPageViewController|XOBaseWebViewController|RegistryBaseViewController|RegistrySectionBaseViewController)')

  backgroundColorPattern = re.compile(r'(\S*backgroundColor\s*=\s*)(UIColor)*(\.)(\w+)')
  iconColorPattern = re.compile(r'(tinted\(\s*|color:\s*)(UIColor)*(\.)*(\w+)')

  labelElementPattern = re.compile(r'')
  iconElementPattern = re.compile(r'(\w+)(.setImage|.image)')

class ColorMapping:
  data = dict()

  def __init__(self):
    with open('/Users/sophieso/Documents/Workspace/ColorMatcher/color-mapping.json') as f:
      self.data = json.load(f)


def main():
  filePaths = searchSwiftFiles()

  allElements = []
  for index, path in enumerate(filePaths):
    print('Analyzing {0}...{1}/{2}'.format(path, index + 1, len(filePaths)))
    
    elementDict = findUIElements(path)
    if elementDict:
      allElements.append(elementDict)

  jsonFile = open('/Users/sophieso/Documents/Workspace/ColorMatcher/result.json', 'w+')
  json.dump(allElements, jsonFile)
  jsonFile.close()
    

def searchSwiftFiles():
  basePath = '/Users/sophieso/Documents/Workspace/TKPlanner-iOS'
  searchPaths = [
    # '/App/**/*.swift',
    # '/GuestServices/**/*.swift',
    # '/Utilities/**/*.swift',
    '/VendorUI/**/*.swift',
    # '/VendorUtilities/**/*.swift',
    # '/WeddingCountdown/**/*.swift',
  ]

  filePaths = []
  for sarchPath in searchPaths:
    result = glob.glob(basePath + sarchPath, recursive=True)
    filePaths += result
  
  return filePaths

def findUIElements(filePath):
  elementList = ElementList()
  with open(filePath) as f:
    read_data = f.read()
    f.closed

    elementList.labels = findLabels(read_data)
    elementList.icons = findIcons(read_data)
    elementList.backgroundColors = findBackgroundColors(read_data)

    mapping = ColorMapping()
    matchIconColors(elementList.icons, mapping)
    matchLabelColors(elementList.labels, mapping)
    matchBackgroundColors(elementList.backgroundColors, mapping)

  updateColors(read_data, elementList, filePath)

  if elementList.totalElementCount() > 0:
    elementDict = {'file': filePath, 'labels': elementList.labels, 'icons': elementList.icons, 'backgroundColors': elementList.backgroundColors}
    return elementDict
    
def updateColors(data, elementList, filePath):
  updatedData = data
  updatedData = updateIconColors(elementList.icons, updatedData)
  updatedData = updateLabelColors(elementList.labels, updatedData)
  updatedData = updateBackgroundColors(elementList.backgroundColors, updatedData)

  with open(filePath, 'w') as f:
    f.write(updatedData)

# label handlers
def findLabels(data):
  labels = []
  result = ElementPattern.labelPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[0]) > 0:
      element = item[0]
      color = searchLabelTextColor(element, data)

      labels.append({'element': element, 'color': color})
  return labels

def searchLabelTextColor(element, fileData):
  colors = []
  pattern = re.compile(r'(%s.textColor\s*=\s*)(UIColor)?(\.)(\w+)' %element)
  result = pattern.findall(fileData)
  for item in result:
    if len(item) > 3 and len(item[3]) > 0:
      colors.append(item[3])

  return colors

def matchLabelColors(elements, mapping):
  textMapping = mapping.data['text']
  for item in elements:
    matchedColors = []
    for color in item['color']:
      originalColor = color
      newColor = ''

      if originalColor in textMapping:
        newColor = textMapping[originalColor]

      matchedColors.append({'original': originalColor, 'new': newColor})

    item['color'] = matchedColors

def updateLabelColors(elements, data):
  updatedData = data
  for item in elements:
    element = item['element']

    for color in item['color']:
      originalColor = color['original']
      newColor = color['new']

      if len(newColor) > 0:
        pattern = re.compile(r'(%s.textColor\s*=\s*)(UIColor)?(\.)%s' %(element, originalColor))
        updatedData = pattern.sub(r'\1\2\3%s' %newColor, updatedData)

  return updatedData

# icon handlers
def findIcons(data):
  icons = []
  result = ElementPattern.iconPattern.findall(data)
  for item in result:
    code = ''.join(item)
    color = []
    element = ''

    if len(item) > 0 and len(item[0]) > 0:
      iconColor = searchIconColor(code)
      if iconColor:
        color.append(iconColor)
      else:
        element = findIconElements(item[0])
        if element:
          color = searchIconTintColor(element, data)

    icons.append({'item': code, 'element': element, 'color': color})
    
  return icons

def searchIconColor(data):
  result = ElementPattern.iconColorPattern.search(data)
  if result:
    groups = result.groups()
    if len(groups) > 3 and len(groups[3]) > 0:
      return groups[3]

def findIconElements(data):
  result = ElementPattern.iconElementPattern.search(data)
  if result:
    groups = result.groups()
    if len(groups) > 0 and len(groups[0]) > 0:
      return groups[0]

def searchIconTintColor(element, fileData):
  colors = []
  pattern = re.compile(r'(%s.tintColor\s*=\s*)(UIColor)?(\.)(\w+)' %element)
  result = pattern.findall(fileData)
  for item in result:
    if len(item) > 3 and len(item[3]) > 0:
      colors.append(item[3])

  return colors

def matchIconColors(elements, mapping):
  iconsMapping = mapping.data['icons']
  for item in elements:
    matchedColors = []

    for color in item['color']:
      originalColor = color
      newColor = ''

      if originalColor in iconsMapping:
        newColor = iconsMapping[originalColor]

      matchedColors.append({'original': originalColor, 'new': newColor})

    item['color'] = matchedColors

def updateIconColors(elements, data):
  updatedData = data
  for item in elements:
    element = item['element']

    for color in item['color']:
      originalColor = color['original']
      newColor = color['new']

      if len(newColor) > 0:
        iconPattern = re.compile(r'(tinted\(\s*|color:\s*)(UIColor)*(\.)*%s' %originalColor)
        updatedData = iconPattern.sub(r'\1\2\3%s' %newColor, updatedData)

        tintPattern = re.compile(r'(%s.tintColor\s*=\s*)(UIColor)?(\.)%s' %(element, originalColor))
        updatedData = tintPattern.sub(r'\1\2\3%s' %newColor, updatedData)

  return updatedData

# cell handlers
def findCells(data):
  cells = []
  result = ElementPattern.cellPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[1]) > 0:
      cells.append(item[1])
    
  return cells

# controller handlers
def matchControllers(data):
  controllers = []
  result = ElementPattern.controllerPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[1]) > 0:
      controllers.append(item[1])
    
  return controllers

# backgroundColor handlers
def findBackgroundColors(data):
  backgroundColors = []
  result = ElementPattern.backgroundColorPattern.findall(data)
  for item in result:
    if len(item) > 1 and len(item[3]) > 0:
      backgroundColors.append({'item': ''.join(item), 'color': item[3]})
    
  return backgroundColors

def matchBackgroundColors(elements, mapping):
  backgroundsMapping = mapping.data['backgrounds']
  for item in elements:
    originalColor = item['color']
    newColor = ''

    if originalColor in backgroundsMapping:
      newColor = backgroundsMapping[originalColor]

    item['color'] = {'original': originalColor, 'new': newColor}

def updateBackgroundColors(elements, data):
  updatedData = data
  for item in elements:
    colorDict = item['color']
    originalColor = colorDict['original']
    newColor = colorDict['new']

    if len(newColor) > 0:
      pattern = re.compile(r'(\S*backgroundColor\s*=\s*)(UIColor)*(\.)%s' %originalColor)
      updatedData = pattern.sub(r'\1\2\3%s' %newColor, updatedData)

  return updatedData
    

main()
